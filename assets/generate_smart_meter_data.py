"""
生成模拟智能电表数据
包含：电压、电流、有功功率、无功功率、功率因数、时间戳
采样频率：1分钟
涵盖多种家用电器：空调、冰箱、热水器、洗衣机、照明、电视等
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random

# 设置随机种子
np.random.seed(42)
random.seed(42)

def generate_appliance_profile():
    """定义各种家用电器的功率特征"""
    profiles = {
        'air_conditioner': {
            'name': '空调',
            'power_range': (800, 1500),  # 运行功率范围 (W)
            'standby_power': 5,  # 待机功率
            'duty_cycle': 0.6,  # 工作占空比
            'cycle_duration': (15, 30),  # 启停周期（分钟）
            'seasonal_factor': {'summer': 1.3, 'winter': 1.2, 'spring': 0.8, 'autumn': 0.8}
        },
        'refrigerator': {
            'name': '冰箱',
            'power_range': (100, 180),
            'standby_power': 5,
            'duty_cycle': 0.3,
            'cycle_duration': (20, 45),
            'seasonal_factor': {'summer': 1.4, 'winter': 0.9, 'spring': 1.0, 'autumn': 1.0}
        },
        'water_heater': {
            'name': '热水器',
            'power_range': (1500, 2000),
            'standby_power': 20,
            'duty_cycle': 0.4,
            'cycle_duration': (10, 25),
            'seasonal_factor': {'summer': 0.7, 'winter': 1.5, 'spring': 1.0, 'autumn': 1.0}
        },
        'washing_machine': {
            'name': '洗衣机',
            'power_range': (200, 500),
            'standby_power': 3,
            'duty_cycle': 0.8,
            'cycle_duration': (30, 60),
            'seasonal_factor': {'summer': 1.0, 'winter': 1.0, 'spring': 1.0, 'autumn': 1.0}
        },
        'lighting': {
            'name': '照明',
            'power_range': (50, 200),
            'standby_power': 0,
            'duty_cycle': 0.5,
            'cycle_duration': (60, 480),
            'seasonal_factor': {'summer': 0.5, 'winter': 1.5, 'spring': 1.0, 'autumn': 1.2}
        },
        'tv': {
            'name': '电视',
            'power_range': (100, 200),
            'standby_power': 2,
            'duty_cycle': 0.6,
            'cycle_duration': (30, 180),
            'seasonal_factor': {'summer': 1.0, 'winter': 1.0, 'spring': 1.0, 'autumn': 1.0}
        },
        'microwave': {
            'name': '微波炉',
            'power_range': (1000, 1400),
            'standby_power': 3,
            'duty_cycle': 0.2,
            'cycle_duration': (2, 10),
            'seasonal_factor': {'summer': 1.0, 'winter': 1.0, 'spring': 1.0, 'autumn': 1.0}
        },
        'electric_stove': {
            'name': '电磁炉',
            'power_range': (1000, 2000),
            'standby_power': 5,
            'duty_cycle': 0.3,
            'cycle_duration': (15, 45),
            'seasonal_factor': {'summer': 1.2, 'winter': 0.8, 'spring': 1.0, 'autumn': 1.0}
        }
    }
    return profiles

def get_seasonal_factor(hour, month):
    """根据时间和月份获取季节因子"""
    if month in [6, 7, 8]:  # 夏季
        return 1.3 if hour >= 12 and hour <= 16 else 1.0
    elif month in [12, 1, 2]:  # 冬季
        return 1.5 if hour >= 6 and hour <= 9 or hour >= 17 and hour <= 21 else 1.0
    else:
        return 1.0

def generate_baseline_power(hour):
    """生成基准功率（基础负载）"""
    # 基础功耗在 50-100W 之间波动
    baseline = 70 + 20 * np.sin(2 * np.pi * hour / 24)
    baseline += np.random.normal(0, 10)
    return max(30, baseline)

def generate_smart_meter_data(start_date, days=30, interval_minutes=1):
    """
    生成智能电表数据
    
    参数:
        start_date: 开始日期
        days: 数据天数
        interval_minutes: 采样间隔（分钟）
    """
    profiles = generate_appliance_profile()
    
    # 计算总采样点数
    total_minutes = days * 24 * 60
    num_samples = total_minutes // interval_minutes
    
    # 生成时间戳
    timestamps = [start_date + timedelta(minutes=i*interval_minutes) 
                  for i in range(num_samples)]
    
    # 初始化功率状态
    appliance_states = {name: {'on': False, 'remaining_cycle': 0} 
                        for name in profiles.keys()}
    
    data = []
    
    for i, ts in enumerate(timestamps):
        hour = ts.hour
        month = ts.month
        seasonal_factor = get_seasonal_factor(hour, month)
        
        # 计算基准功率
        total_power = generate_baseline_power(hour)
        total_reactive_power = total_power * 0.3  # 假设功率因数约0.95
        
        # 更新每个电器的状态
        for name, profile in profiles.items():
            state = appliance_states[name]
            
            # 如果周期结束，随机决定是否开启
            if state['remaining_cycle'] <= 0:
                # 基于占空比和使用习惯决定是否开启
                usage_prob = profile['duty_cycle']
                
                # 添加使用习惯（特定时间段更可能使用）
                if name == 'air_conditioner' and hour >= 12 and hour <= 15:
                    usage_prob *= 1.5
                elif name == 'air_conditioner' and hour >= 22 or hour <= 6:
                    usage_prob *= 1.2
                elif name == 'water_heater' and (hour >= 6 and hour <= 8 or hour >= 19 and hour <= 22):
                    usage_prob *= 2.0
                elif name == 'washing_machine' and hour >= 9 and hour <= 12:
                    usage_prob *= 2.0
                elif name == 'lighting' and (hour >= 18 and hour <= 23 or hour >= 6 and hour <= 7):
                    usage_prob *= 1.8
                elif name == 'tv' and hour >= 19 and hour <= 23:
                    usage_prob *= 1.5
                    
                usage_prob = min(usage_prob, 0.95)  # 最多95%概率
                
                if random.random() < usage_prob:
                    state['on'] = True
                    # 设定本次运行周期
                    cycle_time = random.randint(*profile['cycle_duration']) // interval_minutes
                    state['remaining_cycle'] = cycle_time
                else:
                    state['on'] = False
                    state['remaining_cycle'] = random.randint(10, 60) // interval_minutes
            else:
                state['remaining_cycle'] -= 1
            
            # 计算该电器的功率
            if state['on']:
                power_range = profile['power_range']
                power = np.random.uniform(power_range[0], power_range[1])
                power *= seasonal_factor * profile['seasonal_factor'].get(
                    ['spring', 'summer', 'autumn', 'winter'][(month % 12) // 3], 1.0
                )
                # 添加功率波动
                power *= (1 + np.random.normal(0, 0.05))
                total_power += power
                total_reactive_power += power * 0.3
        
        # 计算电压和电流（假设220V）
        voltage = 220 + np.random.normal(0, 5)
        current = total_power / voltage if voltage > 0 else 0
        
        # 计算功率因数
        power_factor = total_power / np.sqrt(total_power**2 + total_reactive_power**2)
        if np.isnan(power_factor):
            power_factor = 0.95
        
        data.append({
            'timestamp': ts.strftime('%Y-%m-%d %H:%M:%S'),
            'voltage': round(voltage, 2),
            'current': round(current, 2),
            'active_power': round(total_power, 2),  # 有功功率 (W)
            'reactive_power': round(total_reactive_power, 2),  # 无功功率 (Var)
            'power_factor': round(power_factor, 3),
            'energy': round(total_power * interval_minutes / 60 / 1000, 4)  # 电能 (kWh)
        })
    
    return pd.DataFrame(data)

def add_anomalies(df, anomaly_rate=0.02):
    """添加异常数据点"""
    anomaly_indices = np.random.choice(df.index, size=int(len(df) * anomaly_rate), replace=False)
    
    for idx in anomaly_indices:
        anomaly_type = random.choice(['voltage_spike', 'power_surge', 'power_dip', 'harmonic'])
        
        if anomaly_type == 'voltage_spike':
            df.loc[idx, 'voltage'] *= random.uniform(1.3, 1.5)
        elif anomaly_type == 'power_surge':
            df.loc[idx, 'active_power'] *= random.uniform(1.5, 2.0)
        elif anomaly_type == 'power_dip':
            df.loc[idx, 'active_power'] *= random.uniform(0.3, 0.5)
        elif anomaly_type == 'harmonic':
            df.loc[idx, 'reactive_power'] *= random.uniform(2.0, 3.0)
            df.loc[idx, 'power_factor'] *= random.uniform(0.6, 0.7)
    
    return df

def main():
    """生成数据并保存"""
    print("开始生成智能电表数据...")
    
    # 生成30天的数据
    start_date = datetime(2024, 1, 1, 0, 0, 0)
    df = generate_smart_meter_data(start_date, days=30, interval_minutes=1)
    
    # 添加异常数据
    df = add_anomalies(df, anomaly_rate=0.015)
    
    # 保存到assets目录
    output_path = '/workspace/projects/assets/smart_meter_data.csv'
    df.to_csv(output_path, index=False)
    
    print(f"数据已保存到: {output_path}")
    print(f"总记录数: {len(df)}")
    print(f"数据时间范围: {df['timestamp'].iloc[0]} 至 {df['timestamp'].iloc[-1]}")
    print(f"\n数据统计:")
    print(df.describe())
    
    return df

if __name__ == '__main__':
    main()
