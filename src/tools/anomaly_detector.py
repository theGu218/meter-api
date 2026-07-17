"""
异常用电检测工具
检测用电异常、电压波动和潜在故障
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, List
from datetime import datetime, timedelta

def detect_voltage_anomalies(df: pd.DataFrame, std_threshold: float = 3.0) -> Dict[str, Any]:
    """
    检测电压异常
    
    参数:
        df: 电表数据DataFrame
        std_threshold: 标准差倍数阈值，超过则为异常
    
    返回:
        电压异常检测结果
    """
    voltage_mean = df['voltage'].mean()
    voltage_std = df['voltage'].std()
    
    # 定义异常范围（国家标准：198V-242V）
    normal_min, normal_max = 198, 242
    
    # 检测超出标准范围的点
    out_of_range_mask = (df['voltage'] < normal_min) | (df['voltage'] > normal_max)
    out_of_range = df.loc[out_of_range_mask].reset_index(drop=True)
    
    # 检测统计异常（超过3个标准差）
    lower_bound = voltage_mean - std_threshold * voltage_std
    upper_bound = voltage_mean + std_threshold * voltage_std
    statistical_mask = (df['voltage'] < lower_bound) | (df['voltage'] > upper_bound)
    statistical_anomalies = df.loc[statistical_mask].reset_index(drop=True)
    
    # 分类异常类型
    low_voltage_mask = df['voltage'] < normal_min
    low_voltage = df.loc[low_voltage_mask].reset_index(drop=True)
    high_voltage_mask = df['voltage'] > normal_max
    high_voltage = df.loc[high_voltage_mask].reset_index(drop=True)
    sag_mask = (df['voltage'] < voltage_mean * 0.9) & (df['voltage'] >= normal_min)
    voltage_sags = df.loc[sag_mask].reset_index(drop=True)
    swell_mask = (df['voltage'] > voltage_mean * 1.1) & (df['voltage'] <= normal_max)
    voltage_swells = df.loc[swell_mask].reset_index(drop=True)
    
    anomalies = []
    if len(out_of_range) > 0:
        out_of_range_sample = out_of_range[['timestamp', 'voltage']].head(5).to_dict('records')
        anomalies.append({
            'type': 'voltage_out_of_range',
            'description': '电压超出标准范围',
            'count': len(out_of_range),
            'percentage': round(len(out_of_range) / len(df) * 100, 2),
            'severity': 'high' if len(out_of_range) / len(df) > 0.05 else 'medium',
            'samples': out_of_range_sample
        })
    
    if len(voltage_sags) > 0:
        sag_sample = voltage_sags[['timestamp', 'voltage']].head(3).to_dict('records')
        anomalies.append({
            'type': 'voltage_sag',
            'description': '电压暂降',
            'count': len(voltage_sags),
            'percentage': round(len(voltage_sags) / len(df) * 100, 2),
            'severity': 'medium',
            'samples': sag_sample
        })
    
    if len(voltage_swells) > 0:
        swell_sample = voltage_swells[['timestamp', 'voltage']].head(3).to_dict('records')
        anomalies.append({
            'type': 'voltage_swell',
            'description': '电压暂升',
            'count': len(voltage_swells),
            'percentage': round(len(voltage_swells) / len(df) * 100, 2),
            'severity': 'medium',
            'samples': swell_sample
        })
    
    return {
        'voltage_stats': {
            'mean': round(voltage_mean, 2),
            'std': round(voltage_std, 2),
            'min': round(df['voltage'].min(), 2),
            'max': round(df['voltage'].max(), 2),
            'normal_range': f'{normal_min}-{normal_max}V'
        },
        'anomalies': anomalies,
        'has_anomalies': len(anomalies) > 0,
        'overall_status': '正常' if len(out_of_range) / len(df) < 0.01 else '需关注'
    }

def detect_power_anomalies(df: pd.DataFrame) -> Dict[str, Any]:
    """
    检测功率异常（用电异常）
    
    参数:
        df: 电表数据DataFrame
    
    返回:
        功率异常检测结果
    """
    # 计算滑动窗口统计
    window_size = 60  # 60分钟窗口
    df_copy = df.copy()
    df_copy['rolling_mean'] = df_copy['active_power'].rolling(window_size, min_periods=1).mean()
    df_copy['rolling_std'] = df_copy['active_power'].rolling(window_size, min_periods=1).std()
    
    # 检测突然的功率变化
    df_copy['power_diff'] = df_copy['active_power'].diff()
    sudden_changes = df_copy[abs(df_copy['power_diff']) > df_copy['active_power'].std() * 3]
    
    # 检测持续高功率
    high_power_threshold = df_copy['active_power'].quantile(0.95)
    sustained_high_power = df_copy[df_copy['active_power'] > high_power_threshold]
    
    # 检测功率突增（可能的非法用电或设备故障）
    power_spikes = df_copy[df_copy['power_diff'] > df_copy['active_power'].std() * 5]
    
    # 检测功率突降
    power_drops = df_copy[df_copy['power_diff'] < -df_copy['active_power'].std() * 5]
    
    anomalies = []
    
    # 分类汇总
    if len(sudden_changes) > 0:
        # 找出连续的异常区间
        anomalies.append({
            'type': 'sudden_power_change',
            'description': '功率突变',
            'count': len(sudden_changes),
            'percentage': round(len(sudden_changes) / len(df) * 100, 2),
            'severity': 'medium',
            'possible_causes': ['设备启停', '线路切换', '瞬时负载变化'],
            'recommendation': '检查是否有大功率设备频繁启停'
        })
    
    if len(power_spikes) > 0:
        anomalies.append({
            'type': 'power_spike',
            'description': '功率突增',
            'count': len(power_spikes),
            'percentage': round(len(power_spikes) / len(df) * 100, 2),
            'severity': 'high',
            'max_spike': round(power_spikes['power_diff'].max(), 2),
            'possible_causes': ['设备故障', '短路隐患', '非法用电'],
            'recommendation': '建议立即检查用电设备，排除故障隐患'
        })
    
    if len(power_drops) > 0:
        anomalies.append({
            'type': 'power_drop',
            'description': '功率突降',
            'count': len(power_drops),
            'percentage': round(len(power_drops) / len(df) * 100, 2),
            'severity': 'medium',
            'max_drop': round(abs(power_drops['power_diff'].min()), 2),
            'possible_causes': ['设备突然停机', '供电中断', '线路虚接'],
            'recommendation': '检查设备运行状态和线路连接'
        })
    
    # 按严重程度分类
    high_severity = [a for a in anomalies if a['severity'] == 'high']
    medium_severity = [a for a in anomalies if a['severity'] == 'medium']
    
    return {
        'power_stats': {
            'mean': round(df['active_power'].mean(), 2),
            'std': round(df['active_power'].std(), 2),
            'min': round(df['active_power'].min(), 2),
            'max': round(df['active_power'].max(), 2),
            'high_power_threshold': round(high_power_threshold, 2)
        },
        'anomalies': anomalies,
        'high_severity_count': len(high_severity),
        'medium_severity_count': len(medium_severity),
        'has_anomalies': len(anomalies) > 0,
        'overall_status': '异常' if len(high_severity) > 0 else '正常'
    }

def detect_consumption_anomalies(df: pd.DataFrame) -> Dict[str, Any]:
    """
    检测用电量异常（与历史或预期对比）
    
    参数:
        df: 电表数据DataFrame
    
    返回:
        用电量异常检测结果
    """
    df = df.copy()
    df['date'] = df['timestamp'].dt.date
    df['hour'] = df['timestamp'].dt.hour
    df['weekday'] = df['timestamp'].dt.dayofweek
    
    # 计算每日用电量
    daily_energy_series = df.groupby('date')['energy'].sum()
    daily_energy_values = np.array(daily_energy_series)
    
    # 计算统计异常
    daily_mean = float(np.mean(daily_energy_values))
    daily_std = float(np.std(daily_energy_values))
    if daily_std > 0:
        z_scores_array = (daily_energy_values - daily_mean) / daily_std
    else:
        z_scores_array = np.zeros(len(daily_energy_values))
    
    # 找出异常天数的索引
    abnormal_indices = np.where(np.abs(z_scores_array) > 2)[0]
    if len(abnormal_indices) > 0:
        abnormal_dates = daily_energy_series.index[abnormal_indices]
        abnormal_days = daily_energy_series.iloc[abnormal_indices]
    else:
        abnormal_dates = []
        abnormal_days = pd.Series(dtype=float)
    
    z_scores_series = pd.Series(z_scores_array, index=daily_energy_series.index)
    
    # 检测周末vs工作日异常
    df['is_weekend'] = df['weekday'].isin([5, 6])
    weekday_avg = df[~df['is_weekend']].groupby('date')['energy'].sum().mean()
    weekend_avg = df[df['is_weekend']].groupby('date')['energy'].sum().mean()
    
    # 工作日异常：如果周末用电反而比工作日多很多
    weekend_vs_weekday_ratio = weekend_avg / weekday_avg if weekday_avg > 0 else 0
    consumption_pattern_anomaly = weekend_vs_weekday_ratio > 1.3  # 周末比工作日多30%以上
    
    anomalies = []
    
    if len(abnormal_days) > 0:
        anomalies.append({
            'type': 'daily_consumption_anomaly',
            'description': '日用电量异常',
            'abnormal_days': len(abnormal_days),
            'details': [
                {
                    'date': str(date),
                    'energy': round(float(energy), 2),
                    'z_score': round(float(z_scores_series.get(date, 0.0)), 2),
                    'deviation': '偏高' if float(z_scores_series.get(date, 0.0)) > 0 else '偏低'
                }
                for date, energy in abnormal_days.items()
            ],
            'possible_causes': ['新增设备', '使用习惯改变', '设备故障', '漏电'],
            'recommendation': '检查当日是否有特殊用电情况'
        })
    
    if consumption_pattern_anomaly:
        anomalies.append({
            'type': 'usage_pattern_anomaly',
            'description': '用电模式异常',
            'weekday_avg': round(weekday_avg, 2),
            'weekend_avg': round(weekend_avg, 2),
            'ratio': round(weekend_vs_weekday_ratio, 2),
            'possible_causes': ['周末有额外电器使用', '工作日不在家', '统计周期内有假期'],
            'recommendation': '核实周末是否有新增电器使用'
        })
    
    return {
        'consumption_stats': {
            'daily_mean': round(float(daily_mean), 2),
            'daily_std': round(float(daily_std), 2),
            'weekday_avg': round(float(weekday_avg), 2),
            'weekend_avg': round(float(weekend_avg), 2)
        },
        'anomalies': anomalies,
        'has_anomalies': len(anomalies) > 0,
        'overall_status': '异常' if len(abnormal_days) > 1 else '正常'
    }

def generate_anomaly_alert_report(df: pd.DataFrame) -> Dict[str, Any]:
    """
    生成综合异常告警报告
    
    参数:
        df: 电表数据DataFrame
    
    返回:
        综合告警报告
    """
    voltage_report = detect_voltage_anomalies(df)
    power_report = detect_power_anomalies(df)
    consumption_report = detect_consumption_anomalies(df)
    
    # 汇总所有告警
    all_anomalies = (
        voltage_report.get('anomalies', []) +
        power_report.get('anomalies', []) +
        consumption_report.get('anomalies', [])
    )
    
    # 按严重程度分类
    high_priority = [a for a in all_anomalies if a.get('severity') == 'high']
    medium_priority = [a for a in all_anomalies if a.get('severity') == 'medium']
    
    # 生成总体告警级别
    if len(high_priority) > 0:
        alert_level = 'high'
        alert_level_desc = '🔴 高'
        alert_message = '检测到严重异常，建议立即处理'
    elif len(medium_priority) > 3:
        alert_level = 'medium'
        alert_level_desc = '🟡 中'
        alert_message = '检测到多处异常，建议关注'
    elif len(all_anomalies) > 0:
        alert_level = 'low'
        alert_level_desc = '🟢 低'
        alert_message = '检测到少量异常，建议观察'
    else:
        alert_level = 'none'
        alert_level_desc = '✅ 正常'
        alert_message = '未检测到明显异常，用电状态正常'
    
    # 生成处理建议
    action_items = []
    for anomaly in all_anomalies[:5]:  # 最多5条
        if 'recommendation' in anomaly:
            action_items.append(anomaly['recommendation'])
    
    return {
        'alert_level': alert_level,
        'alert_level_description': alert_level_desc,
        'summary_message': alert_message,
        'statistics': {
            'total_anomalies': len(all_anomalies),
            'high_priority': len(high_priority),
            'medium_priority': len(medium_priority),
            'voltage_anomalies': len(voltage_report.get('anomalies', [])),
            'power_anomalies': len(power_report.get('anomalies', [])),
            'consumption_anomalies': len(consumption_report.get('anomalies', []))
        },
        'voltage_status': voltage_report['overall_status'],
        'power_status': power_report['overall_status'],
        'consumption_status': consumption_report['overall_status'],
        'detailed_anomalies': all_anomalies[:10],  # 最多返回10条详细异常
        'recommended_actions': action_items
    }
