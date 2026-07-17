"""
设备能效评估工具
评估家用电器的能效等级和使用效率
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, List

# 常见家用电器的能效标准
EFFICIENCY_STANDARDS = {
    '空调': {
        'excellent': {'COP': 3.6, 'power_range': (800, 1200)},  # COP: 能效比
        'good': {'COP': 3.2, 'power_range': (1200, 1500)},
        'fair': {'COP': 2.8, 'power_range': (1500, 2000)},
        'poor': {'COP': 2.4, 'power_range': (2000, 3000)}
    },
    '冰箱': {
        'excellent': {'daily_kwh': 0.5, 'power_range': (80, 120)},
        'good': {'daily_kwh': 0.8, 'power_range': (120, 150)},
        'fair': {'daily_kwh': 1.2, 'power_range': (150, 180)},
        'poor': {'daily_kwh': 1.8, 'power_range': (180, 250)}
    },
    '热水器': {
        'excellent': {'daily_kwh': 3.0, 'power_range': (1500, 1800)},
        'good': {'daily_kwh': 5.0, 'power_range': (1800, 2200)},
        'fair': {'daily_kwh': 7.0, 'power_range': (2200, 2500)},
        'poor': {'daily_kwh': 10.0, 'power_range': (2500, 3000)}
    },
    '洗衣机': {
        'excellent': {'per_kg': 0.15, 'power_range': (200, 400)},
        'good': {'per_kg': 0.25, 'power_range': (400, 500)},
        'fair': {'per_kg': 0.35, 'power_range': (500, 600)},
        'poor': {'per_kg': 0.50, 'power_range': (600, 800)}
    },
    '电视': {
        'excellent': {'power_per_inch': 0.1, 'power_range': (80, 150)},
        'good': {'power_per_inch': 0.15, 'power_range': (150, 200)},
        'fair': {'power_per_inch': 0.2, 'power_range': (200, 250)},
        'poor': {'power_per_inch': 0.3, 'power_range': (250, 350)}
    }
}

def calculate_appliance_efficiency(df: pd.DataFrame, appliance_name: str) -> Dict[str, Any]:
    """
    计算单个电器的能效
    
    参数:
        df: 电表数据DataFrame
        appliance_name: 电器名称
    
    返回:
        能效评估结果
    """
    if appliance_name not in EFFICIENCY_STANDARDS:
        return {
            'error': f'暂无 {appliance_name} 的能效标准数据',
            'appliance': appliance_name
        }
    
    standard = EFFICIENCY_STANDARDS[appliance_name]
    
    # 计算该功率范围内的数据
    power_min, power_max = standard.get('excellent', standard.get('good', {})).get('power_range', (100, 2000))
    appliance_data = df[(df['active_power'] >= power_min * 0.8) & (df['active_power'] <= power_max * 1.2)]
    
    if len(appliance_data) == 0:
        return {
            'appliance': appliance_name,
            'status': '未检测到该设备运行',
            'estimated_usage': 0
        }
    
    # 计算能效指标
    avg_power = appliance_data['active_power'].mean()
    total_energy = appliance_data['energy'].sum()
    operating_hours = len(appliance_data) / 60  # 假设1分钟一条数据
    
    # 确定能效等级
    efficiency_level = 'unknown'
    efficiency_score = 0
    
    for level in ['excellent', 'good', 'fair', 'poor']:
        if level in standard:
            level_power_range = standard[level]['power_range']
            if level_power_range[0] <= avg_power <= level_power_range[1]:
                efficiency_level = level
                efficiency_score = {'excellent': 95, 'good': 80, 'fair': 65, 'poor': 50}[level]
                break
    
    # 生成评估建议
    suggestions = []
    if efficiency_level == 'poor':
        suggestions.append('建议更换为能效更高的设备')
        suggestions.append('检查设备是否需要维护保养')
    elif efficiency_level == 'fair':
        suggestions.append('设备能效一般，考虑升级换代')
        suggestions.append('注意合理使用，避免长时间满载运行')
    elif efficiency_level == 'good':
        suggestions.append('设备能效良好')
        suggestions.append('继续保持合理使用习惯')
    elif efficiency_level == 'excellent':
        suggestions.append('设备能效优秀')
        suggestions.append('继续保持')
    
    return {
        'appliance': appliance_name,
        'efficiency_level': efficiency_level,
        'efficiency_score': efficiency_score,
        'avg_power': round(avg_power, 2),
        'total_energy': round(total_energy, 2),
        'estimated_daily_usage': round(total_energy / 30, 2),  # 假设数据覆盖30天
        'operating_hours': round(operating_hours, 1),
        'suggestions': suggestions
    }

def evaluate_overall_efficiency(df: pd.DataFrame) -> Dict[str, Any]:
    """
    评估整体能效水平
    
    参数:
        df: 电表数据DataFrame
    
    返回:
        整体能效评估结果
    """
    # 计算各种指标
    total_energy = df['energy'].sum()
    avg_power = df['active_power'].mean()
    peak_power = df['active_power'].max()
    base_load = df[df['active_power'] < 100]['active_power'].mean()
    
    # 能效比 (Energy Efficiency Ratio)
    # 理想情况下，有用功/总功越接近1越好
    energy_utilization = total_energy / (avg_power * len(df) / 60) if avg_power > 0 else 0
    
    # 负载率 (Load Factor)
    # 实际平均功率 / 最大功率，越接近1说明负载越稳定
    load_factor = avg_power / peak_power if peak_power > 0 else 0
    
    # 基载比 (Base Load Ratio)
    # 基线负载占总负载的比例，越低说明设备利用越充分
    base_load_ratio = base_load / avg_power if avg_power > 0 else 0
    
    # 计算综合能效分数 (0-100)
    efficiency_score = (
        energy_utilization * 40 +  # 能源利用率 (40%)
        load_factor * 35 +         # 负载稳定性 (35%)
        (1 - base_load_ratio) * 25  # 设备利用率 (25%)
    ) * 100
    efficiency_score = min(100, max(0, efficiency_score))
    
    # 能效等级
    if efficiency_score >= 85:
        level = 'excellent'
        level_desc = '优秀'
    elif efficiency_score >= 70:
        level = 'good'
        level_desc = '良好'
    elif efficiency_score >= 55:
        level = 'fair'
        level_desc = '一般'
    else:
        level = 'poor'
        level_desc = '较差'
    
    # 生成改进建议
    improvement_suggestions = []
    
    if load_factor < 0.5:
        improvement_suggestions.append('负载波动较大，建议优化用电设备运行时间')
        improvement_suggestions.append('考虑安装储能设备，平滑用电曲线')
    
    if base_load_ratio > 0.3:
        improvement_suggestions.append('基础负载较高，建议检查是否存在待机功耗')
        improvement_suggestions.append('使用智能插座，减少待机能耗')
    
    if peak_power > avg_power * 3:
        improvement_suggestions.append('峰值功率过高，建议分散用电高峰')
        improvement_suggestions.append('避免同时使用多个大功率设备')
    
    if not improvement_suggestions:
        improvement_suggestions.append('能效表现良好，继续保持')
    
    return {
        'overall_score': round(efficiency_score, 1),
        'efficiency_level': level,
        'level_description': level_desc,
        'metrics': {
            'energy_utilization': round(energy_utilization, 3),
            'load_factor': round(load_factor, 3),
            'base_load_ratio': round(base_load_ratio, 3)
        },
        'power_stats': {
            'average_power': round(float(avg_power), 2),
            'peak_power': round(float(peak_power), 2),
            'base_load': round(float(base_load), 2) if isinstance(base_load, (int, float)) and not pd.isna(base_load) else 0,
            'total_energy': round(float(total_energy), 2)
        },
        'improvement_suggestions': improvement_suggestions
    }

def compare_efficiency_by_time(df: pd.DataFrame) -> Dict[str, Any]:
    """
    按时间段对比能效
    
    参数:
        df: 电表数据DataFrame
    
    返回:
        分时段能效对比结果
    """
    df = df.copy()
    df['hour'] = df['timestamp'].dt.hour
    df['period'] = df['hour'].apply(lambda x: 
        '凌晨' if 0 <= x < 6 else
        '上午' if 6 <= x < 12 else
        '下午' if 12 <= x < 18 else
        '晚间'
    )
    
    period_stats = df.groupby('period').agg({
        'active_power': ['mean', 'std', 'max'],
        'energy': 'sum',
        'power_factor': 'mean'
    }).round(2)
    
    period_stats.columns = ['avg_power', 'power_std', 'peak_power', 
                           'total_energy', 'avg_power_factor']
    period_stats = period_stats.reset_index()
    
    # 计算每个时段的能效分数
    period_efficiency = []
    for _, row in period_stats.iterrows():
        score = 100
        # 功率因数扣分
        if row['avg_power_factor'] < 0.9:
            score -= (0.9 - row['avg_power_factor']) * 50
        # 波动性扣分
        if row['power_std'] > row['avg_power'] * 0.5:
            score -= 10
        
        period_efficiency.append({
            'period': row['period'],
            'avg_power': row['avg_power'],
            'peak_power': row['peak_power'],
            'total_energy': row['total_energy'],
            'efficiency_score': max(0, round(score, 1))
        })
    
    # 找出最经济和最浪费的时段
    best_period = min(period_efficiency, key=lambda x: x['avg_power'])
    worst_period = max(period_efficiency, key=lambda x: x['avg_power'])
    
    return {
        'period_breakdown': period_efficiency,
        'best_period': {
            'name': best_period['period'],
            'avg_power': best_period['avg_power'],
            'efficiency_score': best_period['efficiency_score']
        },
        'worst_period': {
            'name': worst_period['period'],
            'avg_power': worst_period['avg_power'],
            'efficiency_score': worst_period['efficiency_score']
        },
        'recommendations': [
            f'建议将大功率设备使用时间调整至 {best_period["period"]}',
            f'{worst_period["period"]} 时段用电效率较低，建议减少该时段用电'
        ]
    }
