import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# 设置随机种子，保证结果可重复
np.random.seed(42)


def generate_scenario_1_typical_day():
    """场景1：典型家庭日用电，总电量约9.55 kWh，平均功率398W"""
    start_time = datetime(2024, 3, 15, 0, 0, 0)
    timestamps = [start_time + timedelta(minutes=i) for i in range(1440)]

    # 基础功率模式 (W)
    base_power = np.zeros(1440)
    # 凌晨 (0-6点): 200W
    base_power[0:360] = 200
    # 早上 (6-9点): 500W
    base_power[360:540] = 500
    # 白天 (9-17点): 300W
    base_power[540:1020] = 300
    # 晚上 (17-22点): 800W
    base_power[1020:1320] = 800
    # 深夜 (22-24点): 250W
    base_power[1320:1440] = 250

    # 添加随机波动 (±15%)
    noise = np.random.normal(0, 0.05, 1440)
    active_power = base_power * (1 + noise)
    active_power = np.clip(active_power, 50, 1500)

    # 电压稳定在220V左右
    voltage = 220 + np.random.normal(0, 2, 1440)
    # 电流 = 功率 / 电压
    current = active_power / voltage
    # 功率因数 0.92~0.98
    power_factor = np.random.uniform(0.92, 0.98, 1440)
    # 无功功率
    reactive_power = active_power * np.tan(np.arccos(power_factor))
    # 电能累计 (kWh) - 每分钟增量 = 功率(W) * 1/60 /1000
    energy_increments = active_power / 60 / 1000
    energy = np.cumsum(energy_increments)

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
    """场景2：包含异常数据，注入指定异常点"""
    # 先生成典型日数据作为基础
    df = generate_scenario_1_typical_day()

    # 注入异常：索引按分钟位置，时间从00:00开始
    # 10:30 -> 索引 10*60+30 = 630
    # 14:15 -> 14*60+15 = 855
    # 18:45 -> 18*60+45 = 1125
    # 22:00 -> 22*60 = 1320

    # 10:30 电压尖峰 (280V+)
    df.loc[630, 'voltage'] = 285.0
    df.loc[630, 'active_power'] = 800  # 稍微提高功率

    # 14:15 功率突增 (2500W+)
    df.loc[855, 'active_power'] = 2600.0
    df.loc[855, 'current'] = 2600 / df.loc[855, 'voltage']

    # 18:45 功率突降 (<100W)
    df.loc[1125, 'active_power'] = 80.0
    df.loc[1125, 'current'] = 80 / df.loc[1125, 'voltage']

    # 22:00 电压暂降 (<190V)
    df.loc[1320, 'voltage'] = 185.0
    df.loc[1320, 'current'] = df.loc[1320, 'active_power'] / 185.0

    # 重新计算受影响的energy（简单用前后均值补一下，避免突变太多）
    for idx in [630, 855, 1125, 1320]:
        # 修正energy increment
        energy_inc = df.loc[idx, 'active_power'] / 60 / 1000
        if idx > 0:
            df.loc[idx, 'energy'] = df.loc[idx - 1, 'energy'] + energy_inc
        else:
            df.loc[idx, 'energy'] = energy_inc
        # 后续重新累加
        for j in range(idx + 1, len(df)):
            inc = df.loc[j, 'active_power'] / 60 / 1000
            df.loc[j, 'energy'] = df.loc[j - 1, 'energy'] + inc

    return df


def generate_scenario_3_weekend():
    """场景3：周末高用电，总电量~18.89 kWh，洗衣机+晚餐高峰"""
    start_time = datetime(2024, 3, 16, 0, 0, 0)  # 周六
    timestamps = [start_time + timedelta(minutes=i) for i in range(1440)]

    base_power = np.zeros(1440)
    # 凌晨: 150W
    base_power[0:480] = 150
    # 洗衣机高峰 (8-12点): 1200W
    base_power[480:720] = 1200
    # 下午 (12-18点): 500W
    base_power[720:1080] = 500
    # 晚餐+电视高峰 (18-22点): 1500W
    base_power[1080:1320] = 1500
    # 深夜: 200W
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
    """场景4：空调周期性启停，功率范围100-1300W"""
    start_time = datetime(2024, 3, 15, 0, 0, 0)
    timestamps = [start_time + timedelta(minutes=i) for i in range(1440)]

    # 模拟空调周期：开30分钟，停15分钟，再开... 全天运行
    active_power = np.zeros(1440)
    cycle = 0
    for i in range(1440):
        if cycle < 30:  # 开启
            active_power[i] = np.random.uniform(1000, 1300)
        elif cycle < 45:  # 关闭（待机功率~100W）
            active_power[i] = np.random.uniform(80, 120)
        else:
            cycle = -1
        cycle += 1
        if cycle == 45:
            cycle = 0

    # 加入一些噪声
    active_power = active_power * (1 + np.random.normal(0, 0.05, 1440))
    active_power = np.clip(active_power, 50, 1400)

    voltage = 220 + np.random.normal(0, 1.5, 1440)
    current = active_power / voltage
    power_factor = np.random.uniform(0.85, 0.92, 1440)  # 空调功率因数略低
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
    """场景5：电能质量问题 - 电压偏低、偏高、功率因数低"""
    start_time = datetime(2024, 3, 15, 0, 0, 0)
    timestamps = [start_time + timedelta(minutes=i) for i in range(1440)]

    # 基础功率模式（类似典型日）
    base_power = np.zeros(1440)
    base_power[0:360] = 200
    base_power[360:540] = 500
    base_power[540:1020] = 350
    base_power[1020:1320] = 700
    base_power[1320:1440] = 250
    noise = np.random.normal(0, 0.05, 1440)
    active_power = base_power * (1 + noise)
    active_power = np.clip(active_power, 50, 1200)

    # 电压异常时段
    voltage = np.full(1440, 220.0)
    # 8:00-10:00 (480-600) 电压偏低 205V
    voltage[480:600] = 205 + np.random.normal(0, 1, 120)
    # 14:00-16:00 (840-960) 电压偏高 235V
    voltage[840:960] = 235 + np.random.normal(0, 1, 120)
    # 其他时段正常波动
    normal_mask = np.ones(1440, dtype=bool)
    normal_mask[480:600] = False
    normal_mask[840:960] = False
    voltage[normal_mask] = 220 + np.random.normal(0, 2, np.sum(normal_mask))
    voltage = np.clip(voltage, 200, 245)

    current = active_power / voltage

    # 功率因数低时段 (18:00-20:00 1080-1200)
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


if __name__ == "__main__":
    # 生成所有场景CSV文件
    print("正在生成测试数据...")
    df1 = generate_scenario_1_typical_day()
    df1.to_csv("scenario_1_typical_day.csv", index=False)
    print("✓ 场景1已生成: scenario_1_typical_day.csv")

    df2 = generate_scenario_2_with_anomalies()
    df2.to_csv("scenario_2_with_anomalies.csv", index=False)
    print("✓ 场景2已生成: scenario_2_with_anomalies.csv")

    df3 = generate_scenario_3_weekend()
    df3.to_csv("scenario_3_weekend.csv", index=False)
    print("✓ 场景3已生成: scenario_3_weekend.csv")

    df4 = generate_scenario_4_air_conditioner()
    df4.to_csv("scenario_4_air_conditioner.csv", index=False)
    print("✓ 场景4已生成: scenario_4_air_conditioner.csv")

    df5 = generate_scenario_5_power_quality()
    df5.to_csv("scenario_5_power_quality.csv", index=False)
    print("✓ 场景5已生成: scenario_5_power_quality.csv")

    print("\n所有测试数据生成完成！")
    print("请将生成的CSV文件放到 /workspace/projects/assets/test_data/ 目录下。")