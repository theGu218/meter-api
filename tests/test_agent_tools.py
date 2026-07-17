"""
测试智能电表能效分析Agent的工具
"""

import sys
sys.path.insert(0, '/workspace/projects/src')

from tools.data_loader import load_meter_data
from tools.appliance_identifier import identify_appliance_by_power
from tools.consumption_analyzer import analyze_daily_consumption
from tools.efficiency_evaluator import evaluate_overall_efficiency
from tools.anomaly_detector import generate_anomaly_alert_report
from tools.chart_generator import generate_power_trend_chart

print("=" * 60)
print("开始测试智能电表能效分析Agent工具")
print("=" * 60)

# 1. 测试数据加载
print("\n[1] 测试数据加载...")
result = load_meter_data(r'E:\project_20260529_163708\projects\assets\test_data\scenario_4_air_conditioner.csv')
if result['success']:
    df = result['data']
    print(f"✅ 数据加载成功")
    print(f"   - 记录数: {len(df)}")
    print(f"   - 时间范围: {result['data_range']['start']} 至 {result['data_range']['end']}")
    print(f"   - 平均功率: {result['stats']['active_power']['mean']} W")
else:
    print(f"❌ 数据加载失败: {result.get('error')}")
    sys.exit(1)

# 2. 测试设备识别
print("\n[2] 测试设备识别...")
test_powers = [1500, 150, 1200, 100, 1800]
for power in test_powers:
    matches = identify_appliance_by_power(power)
    if matches:
        print(f"   {power}W → 识别为: {matches[0]['appliance']} (置信度: {matches[0]['confidence']}%)")
    else:
        print(f"   {power}W → 未识别")

# 3. 测试用电分析
print("\n[3] 测试用电分析...")
daily_stats = analyze_daily_consumption(df)
print(f"✅ 日用电分析完成")
print(f"   - 日均用电: {daily_stats['summary']['avg_daily_energy']} kWh")
print(f"   - 最高日: {daily_stats['summary']['max_consumption_day']['date']}")

# 4. 测试能效评估
print("\n[4] 测试能效评估...")
efficiency = evaluate_overall_efficiency(df)
print(f"✅ 能效评估完成")
print(f"   - 综合评分: {efficiency['overall_score']}/100")
print(f"   - 能效等级: {efficiency['level_description']}")
print(f"   - 负载率: {efficiency['metrics']['load_factor']}")

# 5. 测试异常检测
print("\n[5] 测试异常检测...")
alert = generate_anomaly_alert_report(df)
print(f"✅ 异常检测完成")
print(f"   - 告警级别: {alert['alert_level_description']}")
print(f"   - 总异常数: {alert['statistics']['total_anomalies']}")
print(f"   - 高优先级: {alert['statistics']['high_priority']}")

# 6. 测试图表生成
print("\n[6] 测试图表生成...")
try:
    chart_path = generate_power_trend_chart(df.tail(60))  # 只生成最近1小时
    print(f"✅ 图表生成成功: {chart_path}")
except Exception as e:
    print(f"❌ 图表生成失败: {e}")

print("\n" + "=" * 60)
print("所有工具测试完成！")
print("=" * 60)
