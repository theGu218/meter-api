"""
用电设备识别工具
基于功率特征识别家用电器类型
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Any
from collections import Counter

# 家用电器的功率特征库
APPLIANCE_FEATURES = {
    '空调': {
        'power_range': (800, 2000),
        'characteristics': ['周期性启停', '高功率', '夏季使用频繁'],
        'typical_duration': (30, 480),  # 分钟
        'usage_pattern': '夏季高峰,昼夜持续'
    },
    '冰箱': {
        'power_range': (80, 200),
        'characteristics': ['持续低功率', '间歇性启动', '全天运行'],
        'typical_duration': (24*60, 24*60*7),  # 全天候
        'usage_pattern': '全年稳定,变化小'
    },
    '热水器': {
        'power_range': (1200, 2500),
        'characteristics': ['高功率即热型', '短时运行', '用水时段集中'],
        'typical_duration': (10, 60),
        'usage_pattern': '早晚用水高峰'
    },
    '洗衣机': {
        'power_range': (200, 600),
        'characteristics': ['周期性运行', '有明显启停', '单次运行时间长'],
        'typical_duration': (30, 90),
        'usage_pattern': '白天使用,工作日规律'
    },
    '微波炉': {
        'power_range': (800, 1800),
        'characteristics': ['短时高功率', '瞬时开关', '功率波动大'],
        'typical_duration': (2, 15),
        'usage_pattern': '餐时使用,随机性强'
    },
    '电视': {
        'power_range': (80, 250),
        'characteristics': ['稳定功率', '长时间运行', '晚间使用高峰'],
        'typical_duration': (60, 300),
        'usage_pattern': '晚间使用高峰'
    },
    '照明': {
        'power_range': (30, 250),
        'characteristics': ['可调节', '时间段明显', '多灯组合'],
        'typical_duration': (30, 480),
        'usage_pattern': '早晚使用,季节影响大'
    },
    '电磁炉': {
        'power_range': (1000, 2500),
        'characteristics': ['高功率', '温度控制型', '餐时使用'],
        'typical_duration': (20, 60),
        'usage_pattern': '餐时使用,功率恒定'
    },
    '电饭煲': {
        'power_range': (500, 1000),
        'characteristics': ['煮饭周期', '保温模式', '规律使用'],
        'typical_duration': (30, 120),
        'usage_pattern': '早晚餐前使用'
    },
    '电暖器': {
        'power_range': (1000, 2000),
        'characteristics': ['高功率', '恒温控制', '冬季使用'],
        'typical_duration': (60, 480),
        'usage_pattern': '冬季使用,夜间持续'
    }
}

def identify_appliance_by_power(power: float) -> List[Dict[str, Any]]:
    """
    根据功率识别可能的电器类型
    
    参数:
        power: 测量功率 (W)
    
    返回:
        匹配的电器列表，按可能性排序
    """
    matches = []
    
    for name, features in APPLIANCE_FEATURES.items():
        power_min, power_max = features['power_range']
        if power_min <= power <= power_max:
            # 计算匹配度
            power_ratio = (power - power_min) / (power_max - power_min)
            confidence = 0.6 + 0.4 * power_ratio  # 基础60% + 距离加成
            matches.append({
                'appliance': name,
                'confidence': round(confidence * 100, 1),
                'power_match': f"{power_min}-{power_max}W",
                'characteristics': features['characteristics'],
                'usage_pattern': features['usage_pattern']
            })
    
    # 按置信度排序
    matches.sort(key=lambda x: x['confidence'], reverse=True)
    return matches[:3]  # 返回前3个最可能的匹配

def identify_appliance_by_segment(segment: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    根据用电时段特征识别电器
    
    参数:
        segment: 用电时段信息字典
    
    返回:
        匹配的电器列表
    """
    avg_power = segment.get('avg_power', 0)
    duration = segment.get('duration_minutes', 0)
    power_change = segment.get('power_change', 0)
    
    matches = []
    
    for name, features in APPLIANCE_FEATURES.items():
        power_min, power_max = features['power_range']
        duration_min, duration_max = features['typical_duration']
        
        # 检查功率范围
        power_match = power_min <= avg_power <= power_max
        
        # 检查持续时间
        duration_match = duration_min <= duration <= duration_max
        
        if power_match:
            confidence = 50
            if duration_match:
                confidence += 30
            if power_change > 100:  # 有明显启停
                confidence += 10
            
            matches.append({
                'appliance': name,
                'confidence': min(confidence, 95),
                'avg_power': avg_power,
                'duration': duration,
                'characteristics': features['characteristics'],
                'usage_pattern': features['usage_pattern'],
                'power_range': f"{power_min}-{power_max}W"
            })
    
    matches.sort(key=lambda x: x['confidence'], reverse=True)
    return matches[:3]

def analyze_appliance_usage(df: pd.DataFrame) -> Dict[str, Any]:
    """
    分析电器使用情况
    
    参数:
        df: 电表数据DataFrame
    
    返回:
        电器使用分析结果
    """
    # 功率阈值划分
    thresholds = [
        (0, 100, '待机/基础负载'),
        (100, 300, '小型电器'),
        (300, 800, '中型电器'),
        (800, 1500, '大型电器'),
        (1500, 3000, '高功率电器')
    ]
    
    usage_distribution = {}
    for low, high, category in thresholds:
        count = len(df[(df['active_power'] >= low) & (df['active_power'] < high)])
        percentage = round(count / len(df) * 100, 2)
        usage_distribution[category] = {
            'count': count,
            'percentage': percentage,
            'power_range': f'{low}-{high}W'
        }
    
    # 识别主要用电时段
    df['hour'] = df['timestamp'].dt.hour
    hourly_avg = df.groupby('hour')['active_power'].mean()
    
    peak_hours = hourly_avg.nlargest(5).index.tolist()
    low_hours = hourly_avg.nsmallest(5).index.tolist()
    
    return {
        'usage_distribution': usage_distribution,
        'peak_hours': [f'{h}:00' for h in peak_hours],
        'low_hours': [f'{h}:00' for h in low_hours],
        'hourly_pattern': {
            str(h): round(power, 2) for h, power in hourly_avg.items()
        }
    }
