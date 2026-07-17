"""
智能电表能效分析 API 服务
接受 CSV/Excel 文件上传，返回综合分析报告
"""
import sys
import os
import tempfile
import pandas as pd
from fastapi import FastAPI, File, UploadFile
from fastapi.responses import JSONResponse

# 确保可以导入 tools 包（src 目录在 projects 下）
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from tools.data_loader import preprocess_meter_dataframe
from tools.consumption_analyzer import analyze_daily_consumption
from tools.efficiency_evaluator import evaluate_overall_efficiency
from tools.anomaly_detector import generate_anomaly_alert_report

app = FastAPI(title="智能电表分析API", version="1.0.0")

@app.post("/analyze")
async def analyze_meter_data(file: UploadFile = File(...)):
    """
    接收电表数据文件（CSV 或 Excel），返回分析结果
    """
    # 1. 读取上传的文件内容
    content = await file.read()
    suffix = file.filename.split('.')[-1].lower()

    # 检查文件类型
    if suffix not in ('csv', 'xls', 'xlsx'):
        return JSONResponse(
            status_code=400,
            content={"success": False, "error": "仅支持 CSV 或 Excel 文件"}
        )

    # 写入临时文件
    with tempfile.NamedTemporaryFile(delete=False, suffix=f".{suffix}") as tmp:
        tmp.write(content)
        tmp_path = tmp.name

    try:
        # 2. 读取为 DataFrame
        if suffix == 'csv':
            raw_df = pd.read_csv(tmp_path)
        else:
            raw_df = pd.read_excel(tmp_path)

        # 3. 数据预处理（统一时间格式等）
        df = preprocess_meter_dataframe(raw_df)

        # 4. 调用各个分析模块
        daily = analyze_daily_consumption(df)
        efficiency = evaluate_overall_efficiency(df)
        anomaly = generate_anomaly_alert_report(df)

        # 5. 组装 JSON 结果（提取关键摘要）
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
                "details": anomaly.get('details', [])[:5]  # 最多返回5条详情
            }
        }
        return result

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": f"分析失败: {str(e)}"}
        )
    finally:
        # 清理临时文件
        os.remove(tmp_path)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)