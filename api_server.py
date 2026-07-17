"""
智能电表能效分析 API 服务
支持直接文件上传和 Coze 文件 URL 两种方式
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

app = FastAPI(title="智能电表分析API", version="1.1.0")


class FileURLRequest(BaseModel):
    """Coze 传入的文件 URL 请求体"""
    file: str  # Coze 会将文件临时 URL 放入此字段


@app.post("/analyze")
async def analyze_meter_data(
    file: Optional[UploadFile] = File(None),
    body: Optional[FileURLRequest] = None
):
    """
    接收电表数据文件（CSV 或 Excel），返回分析结果。
    支持两种方式：
    1. 传统文件上传（multipart/form-data）
    2. Coze 传入文件 URL（JSON body）
    """
    tmp_path = None
    try:
        # 1. 处理文件来源：上传文件 或 Coze URL
        if file is not None:
            # 传统文件上传
            content = await file.read()
            suffix = file.filename.split('.')[-1].lower()
            if suffix not in ('csv', 'xls', 'xlsx'):
                return JSONResponse(
                    status_code=400,
                    content={"success": False, "error": "仅支持 CSV 或 Excel 文件"}
                )
            with tempfile.NamedTemporaryFile(delete=False, suffix=f".{suffix}") as tmp:
                tmp.write(content)
                tmp_path = tmp.name

        elif body is not None:
            # Coze 传入文件 URL
            file_url = body.file
            # 提取后缀（处理可能的查询参数）
            suffix = file_url.split('.')[-1].split('?')[0].lower()
            if suffix not in ('csv', 'xls', 'xlsx'):
                return JSONResponse(
                    status_code=400,
                    content={"success": False, "error": "仅支持 CSV 或 Excel 文件"}
                )
            # 下载文件
            resp = requests.get(file_url, timeout=30)
            resp.raise_for_status()
            with tempfile.NamedTemporaryFile(delete=False, suffix=f".{suffix}") as tmp:
                tmp.write(resp.content)
                tmp_path = tmp.name

        else:
            return JSONResponse(
                status_code=400,
                content={"success": False, "error": "未提供文件，请上传文件或提供文件 URL"}
            )

        # 2. 读取为 DataFrame
        if suffix == 'csv':
            df = pd.read_csv(tmp_path)
        else:
            df = pd.read_excel(tmp_path)

        # 3. 数据预处理
        df = preprocess_meter_dataframe(df)

        # 4. 调用各个分析模块
        daily = analyze_daily_consumption(df)
        efficiency = evaluate_overall_efficiency(df)
        anomaly = generate_anomaly_alert_report(df)

        # 5. 组装返回结果
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
            }
        }
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


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)