import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# ===== 配置输出目录 =====
# 使用绝对路径，确保文件生成到测试套件期望的位置
PROJECT_ROOT = r'E:\project_20260529_163708\projects'
OUTPUT_DIR = os.path.join(PROJECT_ROOT, 'assets', 'test_data')
os.makedirs(OUTPUT_DIR, exist_ok=True)

print(f"输出目录: {OUTPUT_DIR}")
print("开始生成测试数据...\n")

np.random.seed(42)

def generate_scenario_1_typical_day():
    """场景1：典型家庭日用电"""
    start_time = datetime(2024, 3, 15, 0, 0, 0)
    timestamps = [start_time + timedelta(minutes=i) for i in range(1440)]
    base_power = np.zeros(1440)
    base_power[0:360] = 200
    base_power[360:540] = 500
    base_power[540:1020] = 300
    base_power[1020:1320] = 800
    base_power[1320:1440] = 250
    noise = np.random.normal(0, 0.05, 1440)
    active_power = base_power * (1 + noise)
    active_power = np.clip(active_power, 50, 1500)
    voltage = 220 + np.random.normal(0, 2, 1440)
    current = active_power / voltage
    power_factor = np.random.uniform(0.92, 0.98, 1440)
    reactive_power = active_power * np.tan(np.arccos(power_factor))
    energy_inc = active_power / 60 / 1000
    energy = np.cumsum(energy_inc)
    df = pd.DataFrame({
        'timestamp': timestamps,
        'voltage': np.round(voltage, 2),
        'current': np.round(current, 3),
        'active_power': np.round(active_power, 1),
        'reactive_power': np.round(reactive_power, 1),
        'power_factor': np.round(power_factor, 3),
        'energy': np.round(energy, 5)
    })
    return df

def generate_scenario_2_with_anomalies():
    df = generate_scenario_1_typical_day()
    # 注入异常（索引按分钟）
    df.loc[630, 'voltage'] = 285.0
    df.loc[855, 'active_power'] = 2600.0
    df.loc[855, 'current'] = 2600 / df.loc[855, 'voltage']
    df.loc[1125, 'active_power'] = 80.0
    df.loc[1125, 'current'] = 80 / df.loc[1125, 'voltage']
    df.loc[1320, 'voltage'] = 185.0
    df.loc[1320, 'current'] = df.loc[1320, 'active_power'] / 185.0
    # 修正能量累计
    for idx in [630, 855, 1125, 1320]:
        energy_inc = df.loc[idx, 'active_power'] / 60 / 1000
        if idx > 0:
            df.loc[idx, 'energy'] = df.loc[idx-1, 'energy'] + energy_inc
        else:
            df.loc[idx, 'energy'] = energy_inc
        for j in range(idx+1, len(df)):
            inc = df.loc[j, 'active_power'] / 60 / 1000
            df.loc[j, 'energy'] = df.loc[j-1, 'energy'] + inc
    return df

def generate_scenario_3_weekend():
    start_time = datetime(2024, 3, 16, 0, 0, 0)
    timestamps = [start_time + timedelta(minutes=i) for i in range(1440)]
    base_power = np.zeros(1440)
    base_power[0:480] = 150
    base_power[480:720] = 1200
    base_power[720:1080] = 500
    base_power[1080:1320] = 1500
    base_power[1320:1440] = 200
    noise = np.random.normal(0, 0.08, 1440)
    active_power = base_power * (1 + noise)
    active_power = np.clip(active_power, 50, 2000)
    voltage = 220 + np.random.normal(0, 2, 1440)
    current = active_power / voltage
    power_factor = np.random.uniform(0.9, 0.97, 1440)
    reactive_power = active_power * np.tan(np.arccos(power_factor))
    energy_inc = active_power / 60 / 1000
    energy = np.cumsum(energy_inc)
    df = pd.DataFrame({
        'timestamp': timestamps,
        'voltage': np.round(voltage, 2),
        'current': np.round(current, 3),
        'active_power': np.round(active_power, 1),
        'reactive_power': np.round(reactive_power, 1),
        'power_factor': np.round(power_factor, 3),
        'energy': np.round(energy, 5)
    })
    return df

def generate_scenario_4_air_conditioner():
    start_time = datetime(2024, 3, 15, 0, 0, 0)
    timestamps = [start_time + timedelta(minutes=i) for i in range(1440)]
    active_power = np.zeros(1440)
    cycle = 0
    for i in range(1440):
        if cycle < 30:
            active_power[i] = np.random.uniform(1000, 1300)
        elif cycle < 45:
            active_power[i] = np.random.uniform(80, 120)
        else:
            cycle = -1
        cycle += 1
        if cycle == 45:
            cycle = 0
    active_power = active_power * (1 + np.random.normal(0, 0.05, 1440))
    active_power = np.clip(active_power, 50, 1400)
    voltage = 220 + np.random.normal(0, 1.5, 1440)
    current = active_power / voltage
    power_factor = np.random.uniform(0.85, 0.92, 1440)
    reactive_power = active_power * np.tan(np.arccos(power_factor))
    energy_inc = active_power / 60 / 1000
    energy = np.cumsum(energy_inc)
    df = pd.DataFrame({
        'timestamp': timestamps,
        'voltage': np.round(voltage, 2),
        'current': np.round(current, 3),
        'active_power': np.round(active_power, 1),
        'reactive_power': np.round(reactive_power, 1),
        'power_factor': np.round(power_factor, 3),
        'energy': np.round(energy, 5)
    })
    return df

def generate_scenario_5_power_quality():
    start_time = datetime(2024, 3, 15, 0, 0, 0)
    timestamps = [start_time + timedelta(minutes=i) for i in range(1440)]
    base_power = np.zeros(1440)
    base_power[0:360] = 200
    base_power[360:540] = 500
    base_power[540:1020] = 350
    base_power[1020:1320] = 700
    base_power[1320:1440] = 250
    noise = np.random.normal(0, 0.05, 1440)
    active_power = base_power * (1 + noise)
    active_power = np.clip(active_power, 50, 1200)
    voltage = np.full(1440, 220.0)
    voltage[480:600] = 205 + np.random.normal(0, 1, 120)
    voltage[840:960] = 235 + np.random.normal(0, 1, 120)
    normal_mask = np.ones(1440, dtype=bool)
    normal_mask[480:600] = False
    normal_mask[840:960] = False
    voltage[normal_mask] = 220 + np.random.normal(0, 2, np.sum(normal_mask))
    voltage = np.clip(voltage, 200, 245)
    current = active_power / voltage
    power_factor = np.random.uniform(0.92, 0.98, 1440)
    power_factor[1080:1200] = np.random.uniform(0.82, 0.87, 120)
    reactive_power = active_power * np.tan(np.arccos(power_factor))
    energy_inc = active_power / 60 / 1000
    energy = np.cumsum(energy_inc)
    df = pd.DataFrame({
        'timestamp': timestamps,
        'voltage': np.round(voltage, 2),
        'current': np.round(current, 3),
        'active_power': np.round(active_power, 1),
        'reactive_power': np.round(reactive_power, 1),
        'power_factor': np.round(power_factor, 3),
        'energy': np.round(energy, 5)
    })
    return df

# 生成所有文件
try:
    df1 = generate_scenario_1_typical_day()
    path1 = os.path.join(OUTPUT_DIR, "scenario_1_typical_day.csv")
    df1.to_csv(path1, index=False)
    print(f"✅ 已生成: {path1}")

    df2 = generate_scenario_2_with_anomalies()
    path2 = os.path.join(OUTPUT_DIR, "scenario_2_with_anomalies.csv")
    df2.to_csv(path2, index=False)
    print(f"✅ 已生成: {path2}")

    df3 = generate_scenario_3_weekend()
    path3 = os.path.join(OUTPUT_DIR, "scenario_3_weekend.csv")
    df3.to_csv(path3, index=False)
    print(f"✅ 已生成: {path3}")

    df4 = generate_scenario_4_air_conditioner()
    path4 = os.path.join(OUTPUT_DIR, "scenario_4_air_conditioner.csv")
    df4.to_csv(path4, index=False)
    print(f"✅ 已生成: {path4}")

    df5 = generate_scenario_5_power_quality()
    path5 = os.path.join(OUTPUT_DIR, "scenario_5_power_quality.csv")
    df5.to_csv(path5, index=False)
    print(f"✅ 已生成: {path5}")

    print("\n🎉 所有CSV文件已成功生成！")
    print(f"请检查目录: {OUTPUT_DIR}")

except Exception as e:
    print(f"\n❌ 生成过程中发生错误: {e}")
    import traceback
    traceback.print_exc()