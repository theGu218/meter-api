"""
工具模块初始化
"""

from .data_loader import load_meter_data, get_power_segments
from .appliance_identifier import identify_appliance_by_power, identify_appliance_by_segment, analyze_appliance_usage
from .consumption_analyzer import (
    analyze_daily_consumption,
    analyze_hourly_consumption,
    analyze_weekly_consumption,
    analyze_power_quality,
    generate_consumption_report
)
from .efficiency_evaluator import (
    calculate_appliance_efficiency,
    evaluate_overall_efficiency,
    compare_efficiency_by_time
)
from .anomaly_detector import (
    detect_voltage_anomalies,
    detect_power_anomalies,
    detect_consumption_anomalies,
    generate_anomaly_alert_report
)
from .chart_generator import (
    generate_power_trend_chart,
    generate_daily_consumption_chart,
    generate_hourly_pattern_chart,
    generate_power_quality_chart,
    generate_efficiency_gauge,
    generate_comprehensive_report
)

__all__ = [
    # 数据加载
    'load_meter_data',
    'get_power_segments',
    # 设备识别
    'identify_appliance_by_power',
    'identify_appliance_by_segment',
    'analyze_appliance_usage',
    # 用电分析
    'analyze_daily_consumption',
    'analyze_hourly_consumption',
    'analyze_weekly_consumption',
    'analyze_power_quality',
    'generate_consumption_report',
    # 能效评估
    'calculate_appliance_efficiency',
    'evaluate_overall_efficiency',
    'compare_efficiency_by_time',
    # 异常检测
    'detect_voltage_anomalies',
    'detect_power_anomalies',
    'detect_consumption_anomalies',
    'generate_anomaly_alert_report',
    # 图表生成
    'generate_power_trend_chart',
    'generate_daily_consumption_chart',
    'generate_hourly_pattern_chart',
    'generate_power_quality_chart',
    'generate_efficiency_gauge',
    'generate_comprehensive_report',
]
