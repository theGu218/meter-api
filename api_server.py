"""
智能电表能效分析 API 服务
- /analyze : 给 Coze 使用，接收 JSON {"file": "文件临时URL"}
- /upload  : 本地测试用，直接上传文件（multipart）
"""
import sys
import os
import tempfile
import requests
import pandas as pd
from fastapi import FastAPI, File, UploadFile
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional

# 确保可以导入 tools 包
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from tools.data_loader import preprocess_meter_dataframe
from tools.consumption_analyzer import analyze_daily_consumption
from tools.efficiency_evaluator import evaluate_overall_efficiency
from tools.anomaly_detector import generate_anomaly_alert_report

app = FastAPI(title="智能电表分析API", version="1.2.0")


class FileURLRequest(BaseModel):
    """Coze 传入的文件 URL 请求体"""
    file: str


def perform_analysis(suffix: str, tmp_path: str):
    """统一的分析逻辑"""
    if suffix == 'csv':
        df = pd.read_csv(tmp_path)
    else:
        df = pd.read_excel(tmp_path)
    df = preprocess_meter_dataframe(df)

    daily = analyze_daily_consumption(df)
    efficiency = evaluate_overall_efficiency(df)
    anomaly = generate_anomaly_alert_report(df)

    return {
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
        }
    }


@app.post("/analyze")
async def analyze_from_url(body: FileURLRequest):
    """
    Coze 专用接口：接收 JSON 格式的文件 URL，下载后分析
    """
    file_url = body.file
    suffix = file_url.split('.')[-1].split('?')[0].lower()
    if suffix not in ('csv', 'xls', 'xlsx'):
        return JSONResponse(
            status_code=400,
            content={"success": False, "error": "仅支持 CSV 或 Excel 文件"}
        )

    tmp_path = None
    try:
        # 下载文件
        resp = requests.get(file_url, timeout=30)
        resp.raise_for_status()
        with tempfile.NamedTemporaryFile(delete=False, suffix=f".{suffix}") as tmp:
            tmp.write(resp.content)
            tmp_path = tmp.name

        result = perform_analysis(suffix, tmp_path)
        return result

    except requests.exceptions.RequestException as e:
        return JSONResponse(
            status_code=400,
            content={"success": False, "error": f"文件下载失败: {str(e)}"}
        )
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": f"分析失败: {str(e)}"}
        )
    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.remove(tmp_path)


@app.post("/upload")
async def analyze_from_upload(file: UploadFile = File(...)):
    """
    本地测试接口：直接上传文件（multipart/form-data）
    """
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
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": f"分析失败: {str(e)}"}
        )
    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.remove(tmp_path)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)