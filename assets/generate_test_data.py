"""
生成测试数据集
包含各种已知模式的用电数据，用于验证Agent的识别和分析能力
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random

np.random.seed(123)
random.seed(123)

def generate_test_data_scenario_1():
    """
    场景1：典型家庭日用电数据
    模拟一天内的典型用电模式
    """
    base_time = datetime(2024, 3, 15, 0, 0, 0)
    records = []
    
    for hour in range(24):
        for minute in range(60):
            timestamp = base_time + timedelta(hours=hour, minutes=minute)
            
            # 根据时段设置基础功率
            if 0 <= hour < 6:  # 深夜 - 仅冰箱待机
                base_power = 80 + np.random.normal(0, 10)
            elif 6 <= hour < 8:  # 早晨 - 热水器、照明
                base_power = 1500 + np.random.normal(0, 100) if 6 <= hour < 7 else 300 + np.random.normal(0, 50)
            elif 8 <= hour < 12:  # 上午 - 基础负载
                base_power = 150 + np.random.normal(0, 30)
            elif 12 <= hour < 14:  # 中午 - 微波炉、冰箱
                base_power = 800 + np.random.normal(0, 100)
            elif 14 <= hour < 18:  # 下午 - 基础负载
                base_power = 120 + np.random.normal(0, 20)
            elif 18 <= hour < 21:  # 晚间 - 电视、照明、空调
                base_power = 1200 + np.random.normal(0, 150)
            else:  # 21-24 - 逐步降低
                base_power = 300 + np.random.normal(0, 50)
            
            voltage = 220 + np.random.normal(0, 3)
            current = base_power / voltage
            power_factor = 0.95 + np.random.normal(0, 0.02)
            
            records.append({
                'timestamp': timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                'voltage': round(voltage, 2),
                'current': round(current, 2),
                'active_power': round(max(50, base_power), 2),
                'reactive_power': round(base_power * 0.3, 2),
                'power_factor': round(min(0.99, max(0.9, power_factor)), 3),
                'energy': round(base_power / 60 / 1000, 4)
            })
    
    return pd.DataFrame(records)

def generate_test_data_scenario_2():
    """
    场景2：包含异常的用电数据
    用于测试异常检测功能
    """
    base_time = datetime(2024, 3, 16, 0, 0, 0)
    records = []
    
    for hour in range(24):
        for minute in range(60):
            timestamp = base_time + timedelta(hours=hour, minutes=minute)
            
            # 正常功率
            base_power = 300 + np.random.normal(0, 50)
            
            # 注入异常
            if hour == 10 and minute == 30:  # 电压尖峰
                voltage = 280 + np.random.normal(0, 5)
            elif hour == 14 and minute == 15:  # 功率突增
                base_power = 2500 + np.random.normal(0, 200)
            elif hour == 18 and minute == 45:  # 功率突降
                base_power = 100 + np.random.normal(0, 20)
            elif hour == 22 and minute == 0:  # 电压暂降
                voltage = 185 + np.random.normal(0, 3)
            else:
                voltage = 220 + np.random.normal(0, 3)
            
            current = base_power / voltage if voltage > 0 else 0
            power_factor = 0.95 + np.random.normal(0, 0.02)
            
            records.append({
                'timestamp': timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                'voltage': round(voltage, 2),
                'current': round(current, 2),
                'active_power': round(max(50, base_power), 2),
                'reactive_power': round(base_power * 0.3, 2),
                'power_factor': round(min(0.99, max(0.9, power_factor)), 3),
                'energy': round(base_power / 60 / 1000, 4)
            })
    
    return pd.DataFrame(records)

def generate_test_data_scenario_3():
    """
    场景3：周末高用电数据
    用于测试周用电对比功能
    """
    base_time = datetime(2024, 3, 17, 0, 0, 0)  # 周日
    records = []
    
    for hour in range(24):
        for minute in range(60):
            timestamp = base_time + timedelta(hours=hour, minutes=minute)
            
            # 周末全天用电较高
            if 0 <= hour < 8:
                base_power = 200 + np.random.normal(0, 30)
            elif 8 <= hour < 12:
                base_power = 1500 + np.random.normal(0, 200)  # 洗衣机
            elif 12 <= hour < 14:
                base_power = 1000 + np.random.normal(0, 150)  # 午餐
            elif 14 <= hour < 18:
                base_power = 400 + np.random.normal(0, 100)
            elif 18 <= hour < 22:
                base_power = 1800 + np.random.normal(0, 200)  # 晚餐+电视
            else:
                base_power = 250 + np.random.normal(0, 40)
            
            voltage = 220 + np.random.normal(0, 3)
            current = base_power / voltage
            power_factor = 0.95 + np.random.normal(0, 0.02)
            
            records.append({
                'timestamp': timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                'voltage': round(voltage, 2),
                'current': round(current, 2),
                'active_power': round(max(50, base_power), 2),
                'reactive_power': round(base_power * 0.3, 2),
                'power_factor': round(min(0.99, max(0.9, power_factor)), 3),
                'energy': round(base_power / 60 / 1000, 4)
            })
    
    return pd.DataFrame(records)

def generate_test_data_scenario_4():
    """
    场景4：单一高功率设备测试
    用于测试设备识别功能
    """
    base_time = datetime(2024, 3, 18, 0, 0, 0)
    records = []
    
    for hour in range(24):
        for minute in range(60):
            timestamp = base_time + timedelta(hours=hour, minutes=minute)
            
            # 模拟空调运行（假设温度较高，空调持续运行）
            if 0 <= hour < 6:  # 深夜低频
                base_power = 900 + np.random.normal(0, 50)
            elif 6 <= hour < 22:  # 白天高频
                # 模拟空调启停
                if random.random() > 0.3:
                    base_power = 1200 + np.random.normal(0, 100)
                else:
                    base_power = 100 + np.random.normal(0, 20)  # 待机
            else:  # 夜间中等
                base_power = 1100 + np.random.normal(0, 80)
            
            voltage = 220 + np.random.normal(0, 3)
            current = base_power / voltage
            power_factor = 0.95 + np.random.normal(0, 0.02)
            
            records.append({
                'timestamp': timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                'voltage': round(voltage, 2),
                'current': round(current, 2),
                'active_power': round(max(50, base_power), 2),
                'reactive_power': round(base_power * 0.3, 2),
                'power_factor': round(min(0.99, max(0.9, power_factor)), 3),
                'energy': round(base_power / 60 / 1000, 4)
            })
    
    return pd.DataFrame(records)

def generate_test_data_scenario_5():
    """
    场景5：电能质量问题数据
    用于测试电能质量分析功能
    """
    base_time = datetime(2024, 3, 19, 0, 0, 0)
    records = []
    
    for hour in range(24):
        for minute in range(60):
            timestamp = base_time + timedelta(hours=hour, minutes=minute)
            
            base_power = 500 + np.random.normal(0, 100)
            
            # 注入电能质量问题
            if 8 <= hour < 10:  # 电压偏低
                voltage = 205 + np.random.normal(0, 5)
            elif 14 <= hour < 16:  # 电压偏高
                voltage = 235 + np.random.normal(0, 5)
            elif 18 <= hour < 20:  # 功率因数低（大量感性负载）
                voltage = 220 + np.random.normal(0, 3)
                power_factor = 0.85 + np.random.normal(0, 0.02)
            else:
                voltage = 220 + np.random.normal(0, 3)
                power_factor = 0.95 + np.random.normal(0, 0.02)
            
            current = base_power / voltage if voltage > 0 else 0
            if 'power_factor' not in dir():
                power_factor = 0.95 + np.random.normal(0, 0.02)
            
            records.append({
                'timestamp': timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                'voltage': round(voltage, 2),
                'current': round(current, 2),
                'active_power': round(max(50, base_power), 2),
                'reactive_power': round(base_power * 0.4 if power_factor < 0.9 else base_power * 0.3, 2),
                'power_factor': round(min(0.99, max(0.8, power_factor)), 3),
                'energy': round(base_power / 60 / 1000, 4)
            })
    
    return pd.DataFrame(records)

def main():
    """生成所有测试数据并保存"""
    print("开始生成测试数据集...")
    
    # 创建测试数据目录
    import os
    test_data_dir = '/workspace/projects/assets/test_data'
    os.makedirs(test_data_dir, exist_ok=True)
    
    # 生成各场景数据
    scenarios = [
        ('scenario_1_typical_day.csv', generate_test_data_scenario_1, '典型家庭日用电'),
        ('scenario_2_with_anomalies.csv', generate_test_data_scenario_2, '包含异常的用电数据'),
        ('scenario_3_weekend.csv', generate_test_data_scenario_3, '周末高用电'),
        ('scenario_4_air_conditioner.csv', generate_test_data_scenario_4, '空调运行数据'),
        ('scenario_5_power_quality.csv', generate_test_data_scenario_5, '电能质量问题数据')
    ]
    
    test_summary = []
    
    for filename, generator, description in scenarios:
        df = generator()
        filepath = os.path.join(test_data_dir, filename)
        df.to_csv(filepath, index=False)
        
        total_energy = df['energy'].sum()
        avg_power = df['active_power'].mean()
        
        test_summary.append({
            'filename': filename,
            'description': description,
            'records': len(df),
            'total_energy_kwh': round(total_energy, 2),
            'avg_power_w': round(avg_power, 2)
        })
        
        print(f"✓ {description}: {filepath}")
    
    # 保存测试数据说明
    readme = """# 智能电表能效分析测试数据集

## 数据集说明

本目录包含5个测试场景，用于验证Agent的各项功能。

### 场景说明

| 场景 | 文件名 | 描述 | 用途 |
|------|--------|------|------|
| 1 | scenario_1_typical_day.csv | 典型家庭日用电 | 验证日常用电分析 |
| 2 | scenario_2_with_anomalies.csv | 包含异常的用电数据 | 验证异常检测功能 |
| 3 | scenario_3_weekend.csv | 周末高用电 | 验证周用电对比 |
| 4 | scenario_4_air_conditioner.csv | 空调运行数据 | 验证设备识别 |
| 5 | scenario_5_power_quality.csv | 电能质量问题数据 | 验证电能质量分析 |

### 字段说明

- timestamp: 时间戳 (YYYY-MM-DD HH:MM:SS)
- voltage: 电压 (V)
- current: 电流 (A)
- active_power: 有功功率 (W)
- reactive_power: 无功功率 (Var)
- power_factor: 功率因数 (0-1)
- energy: 电能 (kWh)

### 测试用例设计

1. **场景1 - 典型家庭日用电**
   - 模拟标准家庭一天内的用电变化
   - 包含：深夜待机、早晚高峰、午间中等
   
2. **场景2 - 包含异常的用电数据**
   - 10:30 - 电压尖峰 (280V+)
   - 14:15 - 功率突增 (2500W+)
   - 18:45 - 功率突降 (<100W)
   - 22:00 - 电压暂降 (<190V)

3. **场景3 - 周末高用电**
   - 8:00-12:00 - 洗衣机运行
   - 18:00-22:00 - 晚餐+电视高峰
   - 全天用电量高于工作日

4. **场景4 - 空调运行数据**
   - 模拟空调的周期性启停
   - 功率范围：100-1300W
   - 用于测试设备识别算法

5. **场景5 - 电能质量问题数据**
   - 8:00-10:00 - 电压偏低 (205V左右)
   - 14:00-16:00 - 电压偏高 (235V左右)
   - 18:00-20:00 - 功率因数低 (<0.87)
"""
    
    with open(os.path.join(test_data_dir, 'README.md'), 'w', encoding='utf-8') as f:
        f.write(readme)
    
    print("\n" + "="*60)
    print("测试数据集生成完成！")
    print("="*60)
    print("\n测试场景汇总:")
    print("-"*60)
    for item in test_summary:
        print(f"{item['description']}")
        print(f"  文件: {item['filename']}")
        print(f"  记录数: {item['records']} 条")
        print(f"  总电量: {item['total_energy_kwh']} kWh")
        print(f"  平均功率: {item['avg_power_w']} W")
        print()
    
    print(f"测试数据目录: {test_data_dir}")

if __name__ == '__main__':
    main()
