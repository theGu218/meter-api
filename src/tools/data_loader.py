"""
数据加载和处理工具
用于加载智能电表数据并进行预处理
"""

import pandas as pd
import numpy as np
from typing import Dict, Any
import os

DATA_PATH = '/workspace/projects/assets/smart_meter_data.csv'

def load_meter_data(file_path: str = DATA_PATH) -> Dict[str, Any]:
    """
    加载智能电表数据
    
    参数:
        file_path: 数据文件路径
    
    返回:
        包含数据和基本信息的字典
    """
    if not os.path.exists(file_path):
        return {
            'success': False,
            'error': f'数据文件不存在: {file_path}',
            'data': None
        }
    
    try:
        df = pd.read_csv(file_path)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        
        # 数据质量检查
        missing_data = df.isnull().sum()
        data_range = {
            'start': df['timestamp'].min().strftime('%Y-%m-%d %H:%M:%S'),
            'end': df['timestamp'].max().strftime('%Y-%m-%d %H:%M:%S'),
            'total_records': len(df),
            'time_interval': '1分钟'
        }
        
        # 基本统计
        stats = {
            'voltage': {
                'mean': round(df['voltage'].mean(), 2),
                'std': round(df['voltage'].std(), 2),
                'min': round(df['voltage'].min(), 2),
                'max': round(df['voltage'].max(), 2)
            },
            'current': {
                'mean': round(df['current'].mean(), 2),
                'std': round(df['current'].std(), 2),
                'min': round(df['current'].min(), 2),
                'max': round(df['current'].max(), 2)
            },
            'active_power': {
                'mean': round(df['active_power'].mean(), 2),
                'std': round(df['active_power'].std(), 2),
                'min': round(df['active_power'].min(), 2),
                'max': round(df['active_power'].max(), 2)
            }
        }
        
        return {
            'success': True,
            'data': df,
            'data_range': data_range,
            'stats': stats,
            'missing_data': missing_data.to_dict()
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': f'加载数据失败: {str(e)}',
            'data': None
        }

def get_power_segments(df: pd.DataFrame, power_threshold: float = 50) -> list:
    """
    识别功率突变点，分割用电时段
    
    参数:
        df: 电表数据DataFrame
        power_threshold: 功率变化阈值 (W)
    
    返回:
        用电时段列表
    """
    df = df.copy()
    df['power_diff'] = df['active_power'].diff().abs()
    
    # 识别突变点（功率变化超过阈值）
    change_points = df[df['power_diff'] > power_threshold].index.tolist()
    change_points = [0] + change_points + [len(df)]
    
    segments = []
    for i in range(len(change_points) - 1):
        start_idx = change_points[i]
        end_idx = change_points[i + 1] - 1
        
        segment_data = df.iloc[start_idx:end_idx + 1]
        if len(segment_data) > 0:
            segments.append({
                'start_time': segment_data['timestamp'].iloc[0],
                'end_time': segment_data['timestamp'].iloc[-1],
                'duration_minutes': len(segment_data),
                'avg_power': round(segment_data['active_power'].mean(), 2),
                'max_power': round(segment_data['active_power'].max(), 2),
                'min_power': round(segment_data['active_power'].min(), 2),
                'power_change': round(segment_data['power_diff'].max(), 2)
            })
    
    return segments
def preprocess_meter_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    对上传的 DataFrame 进行基本预处理：
    - 时间列解析
    - 可根据需要补充其他清洗步骤
    """
    # 解析时间列（假设列名为 timestamp）
    if 'timestamp' in df.columns:
        df['timestamp'] = pd.to_datetime(df['timestamp'])
    # 可以在这里添加更多处理，如去除完全空白的行等
    return df