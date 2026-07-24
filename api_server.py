"""
智能电表能效分析 API 服务
- /analyze : Coze 专用，接收 JSON {"file": "文件临时URL"}
- /upload  : 本地测试，直接上传文件（备用）
"""
import sys
import os
import tempfile
import traceback
import math
import base64
import io
import requests
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from fastapi import FastAPI, File, UploadFile
from fastapi.responses import JSONResponse
from pydantic import BaseModel

# 确保可以导入 tools 包
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from tools.data_loader import preprocess_meter_dataframe
from tools.consumption_analyzer import analyze_daily_consumption
from tools.efficiency_evaluator import evaluate_overall_efficiency
from tools.anomaly_detector import generate_anomaly_alert_report

app = FastAPI(title="智能电表分析API", version="1.7.0")


class FileURLRequest(BaseModel):
    """Coze 传入的文件 URL 请求体"""
    file: str


def clean_nan(obj):
    """递归地将对象中的 NaN/NaT 替换为 None，使其可 JSON 序列化"""
    if isinstance(obj, float):
        if math.isnan(obj) or math.isinf(obj):
            return None
        return obj
    elif isinstance(obj, dict):
        return {k: clean_nan(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [clean_nan(v) for v in obj]
    elif isinstance(obj, np.generic):
        if np.issubdtype(obj, np.floating) and (np.isnan(obj) or np.isinf(obj)):
            return None
        return obj.item()
    return obj


def generate_chart_base64(df: pd.DataFrame, points: int = 200) -> str:
    """
    生成功率趋势图的 Base64 编码字符串。
    参数:
        df: 包含 'timestamp' 和 'active_power' 列的数据
        points: 最多绘制多少个数据点（防止图片过密）
    返回:
        Base64 编码的图片字符串，失败时返回 None
    """
    try:
        plot_df = df.tail(points).copy()
        plt.figure(figsize=(10, 4))
        plt.plot(plot_df['timestamp'], plot_df['active_power'], color='blue', linewidth=0.8)
        plt.title('Power Trend', fontsize=14)
        plt.xlabel('Time')
        plt.ylabel('Active Power (W)')
        plt.xticks(rotation=45)
        plt.tight_layout()

        buf = io.BytesIO()
        plt.savefig(buf, format='png', dpi=100)
        plt.close()
        buf.seek(0)
        return base64.b64encode(buf.read()).decode('utf-8')
    except Exception as e:
        print(f"Chart generation failed: {e}", flush=True)
        return None


def perform_analysis(suffix: str, tmp_path: str):
    """统一的分析逻辑，自动兼容 CSV 和 Excel"""
    try:
        if suffix in ('xls', 'xlsx'):
            df = pd.read_excel(tmp_path)
        else:
            df = pd.read_csv(tmp_path)
    except Exception:
        if suffix in ('xls', 'xlsx'):
            df = pd.read_csv(tmp_path)
        else:
            df = pd.read_excel(tmp_path)

    df = preprocess_meter_dataframe(df)

    daily = analyze_daily_consumption(df)
    efficiency = evaluate_overall_efficiency(df)
    anomaly = generate_anomaly_alert_report(df)

    # 生成图表 Base64
    chart_base64 = generate_chart_base64(df)

    result = {
        "success": True,
        "data_summary": {
            "total_records": len(df),
            "time_range": {
                "start": df['timestamp'].min().strftime('%Y-%m-%d %H:%M:%S'),
                "end": df['timestamp'].max().strftime('%Y-%m-%d %H:%M:%S')
            }
        },
        "daily_analysis": daily.get('summary', {}),
        "efficiency": {
            "score": efficiency.get('overall_score'),
            "level": efficiency.get('level_description')
        },
        "anomaly": {
            "total": anomaly.get('statistics', {}).get('total_anomalies'),
            "high_priority": anomaly.get('statistics', {}).get('high_priority'),
            "level": anomaly.get('alert_level_description'),
            "details": anomaly.get('details', [])[:5]
        },
        "chart_base64": chart_base64   # 新增字段
    }
    # 清理 NaN 值
    return clean_nan(result)


@app.post("/analyze")
async def analyze_from_url(body: FileURLRequest):
    """
    Coze 专用接口：接收 JSON 格式的文件 URL，下载后分析
    """
    print("=" * 40, flush=True)
    print("Coze request received", flush=True)
    print(f"File URL: {body.file}", flush=True)

    file_url = body.file
    tmp_path = None
    try:
        resp = requests.get(file_url, timeout=30, headers={
            "User-Agent": "Mozilla/5.0"
        })
        resp.raise_for_status()
        content = resp.content
        print(f"Downloaded {len(content)} bytes", flush=True)

        preview = content[:200]
        print(f"File preview: {preview}", flush=True)

        content_type = resp.headers.get('Content-Type', '')
        if 'csv' in content_type:
            suffix = 'csv'
        elif 'excel' in content_type or 'spreadsheet' in content_type:
            suffix = 'xlsx'
        else:
            suffix = file_url.split('.')[-1].split('?')[0].lower()
            if suffix not in ('csv', 'xls', 'xlsx'):
                suffix = 'csv'

        with tempfile.NamedTemporaryFile(delete=False, suffix=f".{suffix}") as tmp:
            tmp.write(content)
            tmp_path = tmp.name

        result = perform_analysis(suffix, tmp_path)
        print("Analysis succeeded", flush=True)
        return result

    except requests.exceptions.RequestException as e:
        print(f"Download error: {e}", flush=True)
        return JSONResponse(
            status_code=400,
            content={"success": False, "error": f"文件下载失败: {str(e)}"}
        )
    except Exception as e:
        error_detail = traceback.format_exc()
        print(f"Analysis error:\n{error_detail}", flush=True)
        return JSONResponse(
            status_code=400,
            content={"success": False, "error": f"分析失败: {str(e)}"}
        )
    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.remove(tmp_path)
            print("Temp file deleted", flush=True)


@app.post("/upload")
async def analyze_from_upload(file: UploadFile = File(...)):
    """
    本地测试接口：直接上传文件（multipart/form-data）
    """
    print("Local upload received", flush=True)
    suffix = file.filename.split('.')[-1].lower()
    if suffix not in ('csv', 'xls', 'xlsx'):
        return JSONResponse(
            status_code=400,
            content={"success": False, "error": "仅支持 CSV 或 Excel 文件"}
        )

    tmp_path = None
    try:
        content = await file.read()
        with tempfile.NamedTemporaryFile(delete=False, suffix=f".{suffix}") as tmp:
            tmp.write(content)
            tmp_path = tmp.name

        result = perform_analysis(suffix, tmp_path)
        return result

    except Exception as e:
        error_detail = traceback.format_exc()
        print(f"Upload error:\n{error_detail}", flush=True)
        return JSONResponse(
            status_code=400,
            content={"success": False, "error": f"分析失败: {str(e)}"}
        )
    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.remove(tmp_path)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)