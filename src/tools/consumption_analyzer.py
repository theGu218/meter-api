"""
用电统计分析工具
提供详细的用电数据分析和统计报告
"""

import pandas as pd
import numpy as np
from typing import Dict, Any
from datetime import datetime

def analyze_daily_consumption(df: pd.DataFrame) -> Dict[str, Any]:
    """
    分析日用电量
    
    参数:
        df: 电表数据DataFrame
    
    返回:
        日用电分析结果
    """
    df['date'] = df['timestamp'].dt.date
    
    daily_stats = df.groupby('date').agg({
        'energy': 'sum',  # 总电能 (kWh)
        'active_power': ['mean', 'max', 'min'],
        'voltage': 'mean',
        'current': 'mean'
    }).round(2)
    
    daily_stats.columns = ['total_energy', 'avg_power', 'max_power', 'min_power', 
                           'avg_voltage', 'avg_current']
    daily_stats = daily_stats.reset_index()
    
    # 计算统计指标
    stats = {
        'total_days': len(daily_stats),
        'avg_daily_energy': round(daily_stats['total_energy'].mean(), 2),
        'max_daily_energy': round(daily_stats['total_energy'].max(), 2),
        'min_daily_energy': round(daily_stats['total_energy'].min(), 2),
        'energy_variance': round(daily_stats['total_energy'].std(), 2),
        'total_energy': round(daily_stats['total_energy'].sum(), 2)
    }
    
    # 找出用电最高和最低的日期
    max_day = daily_stats.loc[daily_stats['total_energy'].idxmax()]
    min_day = daily_stats.loc[daily_stats['total_energy'].idxmin()]
    
    stats['max_consumption_day'] = {
        'date': str(max_day['date']),
        'energy': round(max_day['total_energy'], 2)
    }
    stats['min_consumption_day'] = {
        'date': str(min_day['date']),
        'energy': round(min_day['total_energy'], 2)
    }
    
    return {
        'summary': stats,
        'daily_details': daily_stats.to_dict('records')
    }

def analyze_hourly_consumption(df: pd.DataFrame) -> Dict[str, Any]:
    """
    分析小时用电模式
    
    参数:
        df: 电表数据DataFrame
    
    返回:
        小时用电分析结果
    """
    df['hour'] = df['timestamp'].dt.hour
    
    hourly_stats = df.groupby('hour').agg({
        'energy': 'sum',
        'active_power': ['mean', 'max', 'std'],
        'voltage': 'mean',
        'current': 'mean'
    }).round(2)
    
    hourly_stats.columns = ['total_energy', 'avg_power', 'max_power', 'power_std',
                            'avg_voltage', 'avg_current']
    hourly_stats = hourly_stats.reset_index()
    
    # 峰谷时段划分
    peak_threshold = hourly_stats['total_energy'].quantile(0.8)
    valley_threshold = hourly_stats['total_energy'].quantile(0.2)
    
    peak_hours = hourly_stats[hourly_stats['total_energy'] >= peak_threshold]['hour'].tolist()
    valley_hours = hourly_stats[hourly_stats['total_energy'] <= valley_threshold]['hour'].tolist()
    
    return {
        'peak_hours': peak_hours,
        'valley_hours': valley_hours,
        'peak_threshold': round(peak_threshold, 2),
        'valley_threshold': round(valley_threshold, 2),
        'hourly_energy': hourly_stats[['hour', 'total_energy']].to_dict('records'),
        'hourly_power_stats': hourly_stats.to_dict('records')
    }

def analyze_weekly_consumption(df: pd.DataFrame) -> Dict[str, Any]:
    """
    分析周用电模式
    
    参数:
        df: 电表DataFrame
    
    返回:
        周用电分析结果
    """
    df['weekday'] = df['timestamp'].dt.dayofweek  # 0=Monday, 6=Sunday
    df['date'] = df['timestamp'].dt.date
    
    weekly_stats = df.groupby(['date', 'weekday']).agg({
        'energy': 'sum'
    }).reset_index()
    
    weekly_stats.columns = ['date', 'weekday', 'total_energy']
    
    # 按星期几分组
    weekday_names = ['周一', '周二', '周三', '周四', '周五', '周六', '周日']
    weekday_stats = weekly_stats.groupby('weekday')['total_energy'].agg(['mean', 'std', 'sum']).round(2)
    weekday_stats['day'] = [weekday_names[i] for i in weekday_stats.index]
    weekday_stats = weekday_stats.reset_index()
    
    # 工作日 vs 周末
    weekly_stats['is_weekend'] = weekly_stats['weekday'].isin([5, 6])
    weekday_avg = weekly_stats[~weekly_stats['is_weekend']]['total_energy'].mean()
    weekend_avg = weekly_stats[weekly_stats['is_weekend']]['total_energy'].mean()
    
    return {
        'weekday_comparison': {
            'weekday_avg': round(weekday_avg, 2),
            'weekend_avg': round(weekend_avg, 2),
            'difference': round(weekend_avg - weekday_avg, 2),
            'difference_percent': round((weekend_avg - weekday_avg) / weekday_avg * 100, 1)
        },
        'daily_breakdown': weekday_stats[['day', 'mean', 'std', 'sum']].to_dict('records')
    }

def analyze_power_quality(df: pd.DataFrame) -> Dict[str, Any]:
    """
    分析电能质量
    
    参数:
        df: 电表数据DataFrame
    
    返回:
        电能质量分析结果
    """
    # 电压质量
    voltage_stats = {
        'mean': round(df['voltage'].mean(), 2),
        'std': round(df['voltage'].std(), 2),
        'min': round(df['voltage'].min(), 2),
        'max': round(df['voltage'].max(), 2),
        'out_of_range_count': len(df[(df['voltage'] < 198) | (df['voltage'] > 242)]),  # 标准±10%
        'out_of_range_percent': round(len(df[(df['voltage'] < 198) | (df['voltage'] > 242)]) / len(df) * 100, 2)
    }
    
    # 电流质量
    current_stats = {
        'mean': round(df['current'].mean(), 2),
        'max': round(df['current'].max(), 2),
        'std': round(df['current'].std(), 2)
    }
    
    # 功率因数
    pf_stats = {
        'mean': round(df['power_factor'].mean(), 3),
        'min': round(df['power_factor'].min(), 3),
        'low_pf_count': len(df[df['power_factor'] < 0.9]),
        'low_pf_percent': round(len(df[df['power_factor'] < 0.9]) / len(df) * 100, 2)
    }
    
    # 有功功率统计
    power_stats = {
        'mean': round(df['active_power'].mean(), 2),
        'std': round(df['active_power'].std(), 2),
        'min': round(df['active_power'].min(), 2),
        'max': round(df['active_power'].max(), 2)
    }
    
    return {
        'voltage': voltage_stats,
        'current': current_stats,
        'power_factor': pf_stats,
        'active_power': power_stats,
        'quality_assessment': {
            'voltage_stability': '良好' if voltage_stats['out_of_range_percent'] < 5 else '需关注',
            'power_factor': '良好' if pf_stats['low_pf_percent'] < 10 else '需改善'
        }
    }

def generate_consumption_report(df: pd.DataFrame) -> str:
    """
    生成综合用电报告
    
    参数:
        df: 电表数据DataFrame
    
    返回:
        格式化报告文本
    """
    daily = analyze_daily_consumption(df)
    hourly = analyze_hourly_consumption(df)
    weekly = analyze_weekly_consumption(df)
    quality = analyze_power_quality(df)
    
    report = f"""
📊 用电统计分析报告
{'='*50}

📅 日用电统计
- 统计周期: {daily['summary']['total_days']} 天
- 总用电量: {daily['summary']['total_energy']} kWh
- 日均用电: {daily['summary']['avg_daily_energy']} kWh
- 最高日用电: {daily['summary']['max_consumption_day']['date']} ({daily['summary']['max_consumption_day']['energy']} kWh)
- 最低日用电: {daily['summary']['min_consumption_day']['date']} ({daily['summary']['min_consumption_day']['energy']} kWh)

⏰ 用电时段分析
- 高峰时段: {', '.join([f'{h}:00' for h in hourly['peak_hours']])}
- 低谷时段: {', '.join([f'{h}:00' for h in hourly['valley_hours']])}
- 峰谷比: {round(max(hourly['hourly_energy'], key=lambda x: x['total_energy'])['total_energy'] / max(0.001, min(hourly['hourly_energy'], key=lambda x: x['total_energy'])['total_energy']), 2)}

📆 周用电对比
- 工作日均值: {weekly['weekday_comparison']['weekday_avg']} kWh
- 周末均值: {weekly['weekday_comparison']['weekend_avg']} kWh
- 差异: {weekly['weekday_comparison']['difference_percent']}%

⚡ 电能质量
- 电压稳定性: {quality['quality_assessment']['voltage_stability']}
  - 平均电压: {quality['voltage']['mean']}V
  - 电压波动: {quality['voltage']['std']}V
  - 越限比例: {quality['voltage']['out_of_range_percent']}%
- 功率因数: {quality['quality_assessment']['power_factor']}
  - 平均功率因数: {quality['power_factor']['mean']}
  - 低功率因数时段: {quality['power_factor']['low_pf_percent']}%
- 平均功率: {quality['active_power']['mean']}W
- 功率波动: {quality['active_power']['std']}W

{'='*50}
"""
    
    return report
