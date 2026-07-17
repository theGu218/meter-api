"""
生成带标签的训练数据集
用于训练家用电器识别模型
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random
import os

np.random.seed(42)
random.seed(42)

# 家用电器特征定义
APPLIANCES = {
    'refrigerator': {
        'name': '冰箱',
        'power_range': (80, 200),
        'cycle_duration': (20, 45),  # 启停周期（分钟）
        'duty_cycle': 0.3,
        'characteristics': ['间歇运行', '全天稳定', '低温环境'],
        'samples': 300
    },
    'air_conditioner': {
        'name': '空调',
        'power_range': (800, 1500),
        'cycle_duration': (15, 30),
        'duty_cycle': 0.6,
        'characteristics': ['周期性启停', '高功率', '温度相关'],
        'samples': 400
    },
    'water_heater': {
        'name': '热水器',
        'power_range': (1500, 2000),
        'cycle_duration': (10, 25),
        'duty_cycle': 0.4,
        'characteristics': ['高功率即热', '短时运行', '用水时段'],
        'samples': 250
    },
    'washing_machine': {
        'name': '洗衣机',
        'power_range': (200, 500),
        'cycle_duration': (30, 60),
        'duty_cycle': 0.8,
        'characteristics': ['周期性运行', '明显启停', '单次长时'],
        'samples': 200
    },
    'microwave': {
        'name': '微波炉',
        'power_range': (1000, 1400),
        'cycle_duration': (2, 10),
        'duty_cycle': 0.2,
        'characteristics': ['短时高功率', '瞬时开关', '功率波动'],
        'samples': 300
    },
    'tv': {
        'name': '电视',
        'power_range': (100, 200),
        'cycle_duration': (60, 180),
        'duty_cycle': 0.6,
        'characteristics': ['稳定功率', '长时间运行', '晚间使用'],
        'samples': 250
    },
    'lighting': {
        'name': '照明',
        'power_range': (30, 200),
        'cycle_duration': (30, 480),
        'duty_cycle': 0.5,
        'characteristics': ['可调节', '时间段明显', '多灯组合'],
        'samples': 300
    },
    'electric_stove': {
        'name': '电磁炉',
        'power_range': (1000, 2000),
        'cycle_duration': (15, 45),
        'duty_cycle': 0.3,
        'characteristics': ['高功率', '温度控制', '餐时使用'],
        'samples': 200
    },
    'rice_cooker': {
        'name': '电饭煲',
        'power_range': (500, 1000),
        'cycle_duration': (30, 120),
        'duty_cycle': 0.5,
        'characteristics': ['煮饭周期', '保温模式', '规律使用'],
        'samples': 200
    },
    'electric_heater': {
        'name': '电暖器',
        'power_range': (1000, 2000),
        'cycle_duration': (60, 480),
        'duty_cycle': 0.7,
        'characteristics': ['高功率', '恒温控制', '冬季使用'],
        'samples': 200
    }
}

def generate_appliance_samples(appliance_id: str, appliance_info: dict, 
                             samples_per_power: int = 20) -> pd.DataFrame:
    """为单个电器生成样本数据"""
    records = []
    power_min, power_max = appliance_info['power_range']
    
    # 在功率范围内均匀采样
    power_levels = np.linspace(power_min, power_max, samples_per_power)
    
    for power_level in power_levels:
        for _ in range(appliance_info['samples'] // samples_per_power):
            # 基础功率特征
            base_power = power_level + np.random.normal(0, power_level * 0.05)
            base_power = max(0, base_power)
            
            # 电压和电流
            voltage = 220 + np.random.normal(0, 5)
            current = base_power / voltage if voltage > 0 else 0
            
            # 功率因数
            pf_base = 0.95 if appliance_id not in ['microwave', 'electric_stove'] else 0.92
            power_factor = pf_base + np.random.normal(0, 0.02)
            power_factor = min(0.99, max(0.85, power_factor))
            
            # 无功功率
            reactive_power = base_power * np.tan(np.arccos(power_factor))
            
            # 时间特征
            hour = random.randint(0, 23)
            is_weekend = random.choice([True, False])
            
            # 持续时间特征
            duration = random.randint(5, 60)  # 分钟
            
            # 功率波动
            power_std = base_power * random.uniform(0.02, 0.1)
            
            records.append({
                'timestamp': f'2024-03-15 {hour:02d}:{random.randint(0,59):02d}:00',
                'appliance_id': appliance_id,
                'appliance_name': appliance_info['name'],
                'power': round(base_power, 2),
                'voltage': round(voltage, 2),
                'current': round(current, 2),
                'power_factor': round(power_factor, 3),
                'reactive_power': round(reactive_power, 2),
                'hour': hour,
                'is_weekend': int(is_weekend),
                'duration_minutes': duration,
                'power_std': round(power_std, 2),
                'power_range_category': 'high' if base_power > 1000 else ('medium' if base_power > 300 else 'low')
            })
    
    return pd.DataFrame(records)

def generate_mixed_samples(n_samples: int = 1000) -> pd.DataFrame:
    """生成混合设备数据（模拟同一时刻多个设备运行）"""
    records = []
    
    for _ in range(n_samples):
        hour = random.randint(0, 23)
        is_weekend = random.choice([True, False])
        
        # 随机选择2-4个设备同时运行
        n_devices = random.randint(2, 4)
        selected_appliances = random.sample(list(APPLIANCES.keys()), n_devices)
        
        total_power = 0
        for appliance_id in selected_appliances:
            info = APPLIANCES[appliance_id]
            power_min, power_max = info['power_range']
            power = np.random.uniform(power_min, power_max)
            total_power += power
        
        voltage = 220 + np.random.normal(0, 5)
        current = total_power / voltage if voltage > 0 else 0
        power_factor = 0.95 + np.random.normal(0, 0.02)
        
        records.append({
            'timestamp': f'2024-03-15 {hour:02d}:{random.randint(0,59):02d}:00',
            'appliance_id': 'mixed',
            'appliance_name': '+'.join([APPLIANCES[a]['name'] for a in selected_appliances]),
            'power': round(total_power, 2),
            'voltage': round(voltage, 2),
            'current': round(current, 2),
            'power_factor': round(min(0.99, max(0.85, power_factor)), 3),
            'reactive_power': round(total_power * 0.3, 2),
            'hour': hour,
            'is_weekend': int(is_weekend),
            'duration_minutes': random.randint(10, 120),
            'power_std': round(total_power * 0.05, 2),
            'power_range_category': 'high' if total_power > 2000 else ('medium' if total_power > 500 else 'low')
        })
    
    return pd.DataFrame(records)

def generate_sequential_samples(n_sequences: int = 100, sequence_length: int = 60) -> pd.DataFrame:
    """生成时序样本（用于序列模型训练）"""
    records = []
    
    for seq_id in range(n_sequences):
        appliance_id = random.choice(list(APPLIANCES.keys()))
        info = APPLIANCES[appliance_id]
        power_min, power_max = info['power_range']
        
        base_power = np.random.uniform(power_min, power_max)
        start_time = datetime(2024, 3, 15, random.randint(0, 23), 0, 0)
        
        for step in range(sequence_length):
            timestamp = start_time + timedelta(minutes=step)
            
            # 添加功率波动
            power = base_power + np.random.normal(0, base_power * 0.05)
            power = max(0, power)
            
            voltage = 220 + np.random.normal(0, 5)
            current = power / voltage if voltage > 0 else 0
            power_factor = 0.95 + np.random.normal(0, 0.02)
            
            records.append({
                'sequence_id': seq_id,
                'timestamp': timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                'step': step,
                'appliance_id': appliance_id,
                'appliance_name': info['name'],
                'power': round(power, 2),
                'voltage': round(voltage, 2),
                'current': round(current, 2),
                'power_factor': round(min(0.99, max(0.85, power_factor)), 3),
                'reactive_power': round(power * 0.3, 2)
            })
    
    return pd.DataFrame(records)

def main():
    """生成所有训练数据"""
    print("="*70)
    print("开始生成训练数据集")
    print("="*70)
    
    train_dir = '/workspace/projects/assets/train_data'
    os.makedirs(train_dir, exist_ok=True)
    
    all_samples = []
    
    # 1. 为每个设备生成独立样本
    print("\n[1] 生成单一设备样本...")
    for appliance_id, info in APPLIANCES.items():
        df = generate_appliance_samples(appliance_id, info)
        filename = f'{appliance_id}_samples.csv'
        df.to_csv(os.path.join(train_dir, filename), index=False)
        all_samples.append(df)
        print(f"   ✓ {info['name']}: {len(df)} 条样本")
    
    # 2. 生成混合设备样本
    print("\n[2] 生成混合设备样本...")
    mixed_df = generate_mixed_samples(1000)
    mixed_df.to_csv(os.path.join(train_dir, 'mixed_samples.csv'), index=False)
    all_samples.append(mixed_df)
    print(f"   ✓ 混合样本: {len(mixed_df)} 条")
    
    # 3. 生成时序样本
    print("\n[3] 生成时序样本...")
    sequential_df = generate_sequential_samples(100, 60)
    sequential_df.to_csv(os.path.join(train_dir, 'sequential_samples.csv'), index=False)
    print(f"   ✓ 时序样本: {len(sequential_df)} 条 ({100}个序列，每序列60步)")
    
    # 4. 合并所有数据
    print("\n[4] 合并训练数据...")
    combined_df = pd.concat(all_samples, ignore_index=True)
    combined_df.to_csv(os.path.join(train_dir, 'all_appliance_data.csv'), index=False)
    print(f"   ✓ 总样本数: {len(combined_df)} 条")
    
    # 5. 生成特征和标签文件
    print("\n[5] 生成特征工程数据...")
    
    # 提取特征
    feature_cols = ['power', 'voltage', 'current', 'power_factor', 
                   'reactive_power', 'hour', 'is_weekend', 'duration_minutes', 'power_std']
    
    # 设备标签映射
    label_mapping = {name: idx for idx, (name, _) in enumerate(APPLIANCES.items())}
    label_mapping['mixed'] = len(APPLIANCES)
    
    # 创建特征矩阵
    features_df = combined_df[feature_cols].copy()
    features_df.to_csv(os.path.join(train_dir, 'features.csv'), index=False)
    
    # 创建标签向量
    labels_df = combined_df['appliance_id'].map(label_mapping).reset_index(drop=True)
    labels_df.to_csv(os.path.join(train_dir, 'labels.csv'), index=False)
    
    print(f"   ✓ 特征数据: {len(features_df)} 条")
    print(f"   ✓ 标签映射: {label_mapping}")
    
    # 6. 生成数据统计
    print("\n" + "="*70)
    print("训练数据生成完成！")
    print("="*70)
    
    stats = combined_df.groupby('appliance_name').agg({
        'power': ['mean', 'std', 'min', 'max'],
        'voltage': 'mean',
        'current': 'mean',
        'power_factor': 'mean'
    }).round(2)
    
    stats.columns = ['功率均值', '功率标准差', '功率最小', '功率最大', 
                   '电压均值', '电流均值', '功率因数均值']
    print("\n各设备统计:")
    print(stats.to_string())
    
    print(f"\n训练数据目录: {train_dir}")
    print("\n文件列表:")
    for f in sorted(os.listdir(train_dir)):
        fpath = os.path.join(train_dir, f)
        size = os.path.getsize(fpath)
        print(f"  - {f} ({size/1024:.1f} KB)")

if __name__ == '__main__':
    main()
