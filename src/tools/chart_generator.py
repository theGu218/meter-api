"""
可视化图表生成工具
生成用电分析相关的图表
"""

import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')  # 使用非交互式后端
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.font_manager import FontProperties
from typing import Dict, Any, List
import os
from datetime import datetime

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['DejaVu Sans', 'SimHei', 'Arial Unicode MS']
plt.rcParams['axes.unicode_minus'] = False

OUTPUT_DIR = '/workspace/projects/assets/charts'

def ensure_output_dir():
    """确保输出目录存在"""
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

def generate_power_trend_chart(df: pd.DataFrame, hours: int = 24) -> str:
    """
    生成功率趋势图
    
    参数:
        df: 电表数据DataFrame
        hours: 显示的小时数（默认24小时）
    
    返回:
        图表文件路径
    """
    ensure_output_dir()
    
    # 取最近N小时数据
    recent_df = df.tail(hours * 60)  # 假设1分钟一条数据
    
    fig, axes = plt.subplots(2, 1, figsize=(14, 10), sharex=True)
    
    # 上图：有功功率
    axes[0].plot(recent_df['timestamp'], recent_df['active_power'], 
                color='#2E86AB', linewidth=1.5, label='Active Power')
    axes[0].fill_between(recent_df['timestamp'], recent_df['active_power'], 
                        alpha=0.3, color='#2E86AB')
    axes[0].axhline(y=recent_df['active_power'].mean(), color='red', 
                   linestyle='--', label=f'Mean: {recent_df["active_power"].mean():.1f}W')
    axes[0].set_ylabel('Power (W)', fontsize=12)
    axes[0].set_title(f'Power Trend - Last {hours} Hours', fontsize=14, fontweight='bold')
    axes[0].legend(loc='upper right')
    axes[0].grid(True, alpha=0.3)
    
    # 下图：电压和电流
    ax2 = axes[1]
    ax2.plot(recent_df['timestamp'], recent_df['voltage'], 
            color='#F18F01', linewidth=1.2, label='Voltage (V)')
    ax2.set_ylabel('Voltage (V)', fontsize=12, color='#F18F01')
    ax2.tick_params(axis='y', labelcolor='#F18F01')
    
    ax3 = ax2.twinx()
    ax3.plot(recent_df['timestamp'], recent_df['current'], 
            color='#C73E1D', linewidth=1.2, label='Current (A)')
    ax3.set_ylabel('Current (A)', fontsize=12, color='#C73E1D')
    ax3.tick_params(axis='y', labelcolor='#C73E1D')
    
    lines1, labels1 = ax2.get_legend_handles_labels()
    lines2, labels2 = ax3.get_legend_handles_labels()
    ax2.legend(lines1 + lines2, labels1 + labels2, loc='upper right')
    
    axes[1].set_xlabel('Time', fontsize=12)
    axes[1].grid(True, alpha=0.3)
    
    # 格式化x轴时间
    axes[1].xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
    axes[1].xaxis.set_major_locator(mdates.AutoDateLocator())
    plt.xticks(rotation=45)
    
    plt.tight_layout()
    
    output_path = os.path.join(OUTPUT_DIR, f'power_trend_{datetime.now().strftime("%Y%m%d_%H%M%S")}.png')
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()
    
    return output_path

def generate_daily_consumption_chart(df: pd.DataFrame) -> str:
    """
    生成日用电量柱状图
    
    参数:
        df: 电表数据DataFrame
    
    返回:
        图表文件路径
    """
    ensure_output_dir()
    
    df = df.copy()
    df['date'] = pd.to_datetime(df['timestamp']).dt.date
    
    daily_energy = df.groupby('date')['energy'].sum().reset_index()
    daily_energy.columns = ['date', 'total_energy']
    
    fig, ax = plt.subplots(figsize=(14, 6))
    
    # 柱状图
    bars = ax.bar(daily_energy['date'], daily_energy['total_energy'], 
                 color='#2E86AB', alpha=0.8, edgecolor='#1a5276')
    
    # 添加数值标签
    for bar, energy in zip(bars, daily_energy['total_energy']):
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height,
               f'{energy:.1f}',
               ha='center', va='bottom', fontsize=9)
    
    # 添加平均值线
    avg_energy = daily_energy['total_energy'].mean()
    ax.axhline(y=avg_energy, color='red', linestyle='--', linewidth=2, 
              label=f'Average: {avg_energy:.1f} kWh')
    
    # 标注最高和最低
    max_idx = daily_energy['total_energy'].idxmax()
    min_idx = daily_energy['total_energy'].idxmin()
    
    bars[max_idx].set_color('#27ae60')  # 绿色标注最高
    bars[min_idx].set_color('#e74c3c')  # 红色标注最低
    
    ax.set_xlabel('Date', fontsize=12)
    ax.set_ylabel('Daily Energy Consumption (kWh)', fontsize=12)
    ax.set_title('Daily Energy Consumption Trend', fontsize=14, fontweight='bold')
    ax.legend(loc='upper right')
    ax.grid(True, axis='y', alpha=0.3)
    
    # 旋转x轴标签
    plt.xticks(rotation=45, ha='right')
    
    # 添加统计信息
    stats_text = f'Total: {daily_energy["total_energy"].sum():.1f} kWh | '
    stats_text += f'Max: {daily_energy["total_energy"].max():.1f} kWh | '
    stats_text += f'Min: {daily_energy["total_energy"].min():.1f} kWh'
    ax.text(0.5, -0.15, stats_text, transform=ax.transAxes, 
           ha='center', fontsize=10, style='italic')
    
    plt.tight_layout()
    
    output_path = os.path.join(OUTPUT_DIR, f'daily_consumption_{datetime.now().strftime("%Y%m%d_%H%M%S")}.png')
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()
    
    return output_path

def generate_hourly_pattern_chart(df: pd.DataFrame) -> str:
    """
    生成24小时用电模式图
    
    参数:
        df: 电表数据DataFrame
    
    返回:
        图表文件路径
    """
    ensure_output_dir()
    
    df = df.copy()
    df['hour'] = pd.to_datetime(df['timestamp']).dt.hour
    
    hourly_stats = df.groupby('hour').agg({
        'active_power': ['mean', 'std', 'min', 'max'],
        'energy': 'sum'
    }).reset_index()
    
    hourly_stats.columns = ['hour', 'avg_power', 'power_std', 'min_power', 'max_power', 'total_energy']
    
    fig, axes = plt.subplots(1, 2, figsize=(16, 6))
    
    # 左图：平均功率曲线
    ax1 = axes[0]
    hours = hourly_stats['hour']
    ax1.plot(hours, hourly_stats['avg_power'], color='#2E86AB', 
            linewidth=2, marker='o', markersize=6, label='Average Power')
    ax1.fill_between(hours, 
                     hourly_stats['avg_power'] - hourly_stats['power_std'],
                     hourly_stats['avg_power'] + hourly_stats['power_std'],
                     alpha=0.2, color='#2E86AB', label='±1 Std Dev')
    
    # 标注峰谷
    peak_hour = hourly_stats.loc[hourly_stats['avg_power'].idxmax(), 'hour']
    valley_hour = hourly_stats.loc[hourly_stats['avg_power'].idxmin(), 'hour']
    
    ax1.annotate(f'Peak: {peak_hour}:00', 
                xy=(peak_hour, hourly_stats['avg_power'].max()),
                xytext=(peak_hour+1, hourly_stats['avg_power'].max()+50),
                fontsize=10, color='red',
                arrowprops=dict(arrowstyle='->', color='red'))
    
    ax1.annotate(f'Valley: {valley_hour}:00', 
                xy=(valley_hour, hourly_stats['avg_power'].min()),
                xytext=(valley_hour+1, hourly_stats['avg_power'].min()-50),
                fontsize=10, color='green',
                arrowprops=dict(arrowstyle='->', color='green'))
    
    ax1.set_xlabel('Hour of Day', fontsize=12)
    ax1.set_ylabel('Power (W)', fontsize=12)
    ax1.set_title('Hourly Power Pattern', fontsize=14, fontweight='bold')
    ax1.set_xticks(range(0, 24, 2))
    ax1.grid(True, alpha=0.3)
    ax1.legend(loc='upper left')
    
    # 右图：时段能耗饼图
    ax2 = axes[1]
    df['period'] = df['hour'].apply(lambda x: 
        'Night (0-6)' if 0 <= x < 6 else
        'Morning (6-12)' if 6 <= x < 12 else
        'Afternoon (12-18)' if 12 <= x < 18 else
        'Evening (18-24)')
    
    period_energy = df.groupby('period')['energy'].sum()
    
    colors = ['#3498db', '#f39c12', '#e74c3c', '#9b59b6']
    explode = (0.05, 0.05, 0.05, 0.05)
    
    wedges, texts, autotexts = ax2.pie(period_energy, labels=period_energy.index, 
                                        autopct='%1.1f%%', colors=colors,
                                        explode=explode, startangle=90)
    
    for autotext in autotexts:
        autotext.set_color('white')
        autotext.set_fontweight('bold')
    
    ax2.set_title('Energy Distribution by Period', fontsize=14, fontweight='bold')
    
    plt.tight_layout()
    
    output_path = os.path.join(OUTPUT_DIR, f'hourly_pattern_{datetime.now().strftime("%Y%m%d_%H%M%S")}.png')
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()
    
    return output_path

def generate_power_quality_chart(df: pd.DataFrame) -> str:
    """
    生成电能质量分析图
    
    参数:
        df: 电表数据DataFrame
    
    返回:
        图表文件路径
    """
    ensure_output_dir()
    
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    
    # 1. 电压分布直方图
    ax1 = axes[0, 0]
    ax1.hist(df['voltage'], bins=50, color='#3498db', alpha=0.7, edgecolor='black')
    ax1.axvline(x=220, color='green', linestyle='--', linewidth=2, label='Standard: 220V')
    ax1.axvline(x=198, color='orange', linestyle='--', linewidth=1.5, label='Min: 198V')
    ax1.axvline(x=242, color='orange', linestyle='--', linewidth=1.5, label='Max: 242V')
    ax1.set_xlabel('Voltage (V)', fontsize=11)
    ax1.set_ylabel('Frequency', fontsize=11)
    ax1.set_title('Voltage Distribution', fontsize=13, fontweight='bold')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # 2. 功率因数分布
    ax2 = axes[0, 1]
    ax2.hist(df['power_factor'], bins=30, color='#2ecc71', alpha=0.7, edgecolor='black')
    ax2.axvline(x=0.95, color='green', linestyle='--', linewidth=2, label='Good: 0.95')
    ax2.axvline(x=0.9, color='orange', linestyle='--', linewidth=1.5, label='Acceptable: 0.90')
    ax2.set_xlabel('Power Factor', fontsize=11)
    ax2.set_ylabel('Frequency', fontsize=11)
    ax2.set_title('Power Factor Distribution', fontsize=13, fontweight='bold')
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    
    # 3. 有功功率vs无功功率散点图
    ax3 = axes[1, 0]
    scatter = ax3.scatter(df['active_power'], df['reactive_power'], 
                          c=df['power_factor'], cmap='RdYlGn', 
                          alpha=0.5, s=10)
    ax3.set_xlabel('Active Power (W)', fontsize=11)
    ax3.set_ylabel('Reactive Power (Var)', fontsize=11)
    ax3.set_title('Active vs Reactive Power (colored by PF)', fontsize=13, fontweight='bold')
    cbar = plt.colorbar(scatter, ax=ax3)
    cbar.set_label('Power Factor')
    ax3.grid(True, alpha=0.3)
    
    # 4. 功率因数随时间变化
    ax4 = axes[1, 1]
    df_sample = df.iloc[::10].copy()  # 每10分钟取一个样本
    ax4.plot(pd.to_datetime(df_sample['timestamp']), df_sample['power_factor'], 
            color='#9b59b6', linewidth=1, alpha=0.8)
    ax4.axhline(y=0.95, color='green', linestyle='--', linewidth=1.5, label='Good: 0.95')
    ax4.axhline(y=0.9, color='orange', linestyle='--', linewidth=1.5, label='Acceptable: 0.90')
    ax4.set_xlabel('Time', fontsize=11)
    ax4.set_ylabel('Power Factor', fontsize=11)
    ax4.set_title('Power Factor Over Time', fontsize=13, fontweight='bold')
    ax4.legend()
    ax4.grid(True, alpha=0.3)
    ax4.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d'))
    
    plt.tight_layout()
    
    output_path = os.path.join(OUTPUT_DIR, f'power_quality_{datetime.now().strftime("%Y%m%d_%H%M%S")}.png')
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()
    
    return output_path

def generate_efficiency_gauge(score: float, metric_name: str) -> str:
    """
    生成能效仪表盘图
    
    参数:
        score: 能效分数 (0-100)
        metric_name: 指标名称
    
    返回:
        图表文件路径
    """
    ensure_output_dir()
    
    fig, ax = plt.subplots(figsize=(8, 6), subplot_kw={'projection': 'polar'})
    
    # 将分数转换为角度 (0-100 -> 180-0度)
    theta = np.linspace(0, np.pi, 100)
    score_angle = np.pi * (1 - score / 100)
    
    # 绘制背景弧
    ax.plot(theta, [1]*100, color='lightgray', linewidth=20, alpha=0.3)
    
    # 绘制分数弧
    score_theta = np.linspace(np.pi, score_angle, 50)
    if score >= 85:
        color = '#27ae60'  # 绿色
    elif score >= 70:
        color = '#f39c12'  # 黄色
    else:
        color = '#e74c3c'  # 红色
    
    ax.plot(score_theta, [1]*50, color=color, linewidth=20)
    
    # 设置刻度
    ax.set_xticks(np.linspace(0, np.pi, 5))
    ax.set_xticklabels(['100', '75', '50', '25', '0'])
    ax.set_ylim(0, 1.3)
    
    # 添加分数文本
    ax.text(np.pi/2, 0.5, f'{score:.1f}', fontsize=48, ha='center', va='center',
           fontweight='bold', color=color)
    ax.text(np.pi/2, 0.2, metric_name, fontsize=16, ha='center', va='center',
           style='italic')
    
    ax.set_title(f'{metric_name} Score', fontsize=18, fontweight='bold', pad=20)
    ax.grid(True, alpha=0.3)
    
    # 移除径向标签
    ax.set_yticklabels([])
    
    plt.tight_layout()
    
    output_path = os.path.join(OUTPUT_DIR, f'efficiency_gauge_{datetime.now().strftime("%Y%m%d_%H%M%S")}.png')
    plt.savefig(output_path, dpi=150, bbox_inches='tight', facecolor='white')
    plt.close()
    
    return output_path

def generate_comprehensive_report(df: pd.DataFrame, efficiency_score: float) -> List[str]:
    """
    生成综合分析报告图表
    
    参数:
        df: 电表数据DataFrame
        efficiency_score: 综合能效分数
    
    返回:
        图表文件路径列表
    """
    charts = []
    
    print("正在生成图表...")
    
    # 1. 功率趋势图
    try:
        path = generate_power_trend_chart(df.tail(24*60))  # 最近24小时
        charts.append(path)
        print(f"✓ 功率趋势图已生成")
    except Exception as e:
        print(f"✗ 功率趋势图生成失败: {e}")
    
    # 2. 日用电量图
    try:
        path = generate_daily_consumption_chart(df)
        charts.append(path)
        print(f"✓ 日用电量图已生成")
    except Exception as e:
        print(f"✗ 日用电量图生成失败: {e}")
    
    # 3. 小时用电模式图
    try:
        path = generate_hourly_pattern_chart(df)
        charts.append(path)
        print(f"✓ 小时用电模式图已生成")
    except Exception as e:
        print(f"✗ 小时用电模式图生成失败: {e}")
    
    # 4. 电能质量图
    try:
        path = generate_power_quality_chart(df)
        charts.append(path)
        print(f"✓ 电能质量图已生成")
    except Exception as e:
        print(f"✗ 电能质量图生成失败: {e}")
    
    # 5. 能效仪表盘
    try:
        path = generate_efficiency_gauge(efficiency_score, 'Overall Efficiency')
        charts.append(path)
        print(f"✓ 能效仪表盘已生成")
    except Exception as e:
        print(f"✗ 能效仪表盘生成失败: {e}")
    
    return charts
