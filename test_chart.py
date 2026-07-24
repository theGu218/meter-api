import pandas as pd
from tools.chart_generator import generate_power_trend_chart

df = pd.read_csv('E:\project_20260529_163708\projects\assets\test_data\scenario_1_typical_day.csv')  # 替换为实际测试文件路径
df['timestamp'] = pd.to_datetime(df['timestamp'])
chart_path = generate_power_trend_chart(df.tail(60))
print(f"图表已保存至: {chart_path}")