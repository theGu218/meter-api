"""
智能电表能效分析Agent
基于智能电表数据，实现设备识别、用能分析和异常告警
"""

import os
import json
from typing import Annotated
from langchain.agents import create_agent
from langchain_openai import ChatOpenAI
from langgraph.graph import MessagesState
from langgraph.graph.message import add_messages
from langchain_core.messages import AnyMessage
from langchain.tools import tool
from langchain.agents.middleware import wrap_tool_call
from langchain.messages import ToolMessage

# Agent配置
LLM_CONFIG = "config/agent_llm_config.json"
MAX_MESSAGES = 40

# 数据路径
DATA_PATH = '/workspace/projects/assets/smart_meter_data.csv'

def _windowed_messages(old, new):
    """滑动窗口: 只保留最近 MAX_MESSAGES 条消息"""
    from langgraph.graph.message import add_messages
    result = add_messages(old, new)
    # 将结果转换为列表后切片
    if hasattr(result, '__iter__'):
        result_list = list(result)
        return result_list[-MAX_MESSAGES:]
    return result

class AgentState(MessagesState):
    messages: Annotated[list[AnyMessage], _windowed_messages]

# ============ 工具定义 ============

@tool
def load_meter_data_tool(file_path: str = DATA_PATH) -> str:
    """
    加载智能电表数据，获取数据的基本信息和统计。
    
    参数:
        file_path: 数据文件路径，默认使用项目自带数据
    
    返回:
        数据加载结果和基本统计信息
    """
    try:
        from tools.data_loader import load_meter_data
        
        result = load_meter_data(file_path)
        
        if not result['success']:
            return f"加载数据失败: {result.get('error', '未知错误')}"
        
        df = result['data']
        stats = result['stats']
        data_range = result['data_range']
        
        output = f"""
✅ 数据加载成功！

📊 数据概览:
- 数据范围: {data_range['start']} 至 {data_range['end']}
- 总记录数: {data_range['total_records']} 条
- 采样间隔: {data_range['time_interval']}

📈 功率统计:
- 平均功率: {stats['active_power']['mean']} W
- 功率范围: {stats['active_power']['min']} - {stats['active_power']['max']} W
- 标准差: {stats['active_power']['std']} W

⚡ 电压统计:
- 平均电压: {stats['voltage']['mean']} V
- 电压范围: {stats['voltage']['min']} - {stats['voltage']['max']} V

🔌 电流统计:
- 平均电流: {stats['current']['mean']} A
- 电流范围: {stats['current']['min']} - {stats['current']['max']} A
"""
        return output
        
    except Exception as e:
        return f"加载数据时出错: {str(e)}"

@tool
def identify_appliance_tool(power_value: float) -> str:
    """
    根据功率值识别可能的家用电器类型。
    
    参数:
        power_value: 测量的功率值 (单位: W)
    
    返回:
        匹配的电器列表和特征信息
    """
    try:
        from tools.appliance_identifier import identify_appliance_by_power, APPLIANCE_FEATURES
        
        if power_value < 0 or power_value > 50000:
            return "功率值超出合理范围 (0-50000W)，请检查输入"
        
        matches = identify_appliance_by_power(power_value)
        
        if not matches:
            return f"未找到与 {power_value}W 匹配的电器类型，可能为非标准设备或测量异常"
        
        output = f"""
🔍 基于功率 {power_value}W 的设备识别结果:

"""
        for i, match in enumerate(matches, 1):
            output += f"{i}. **{match['appliance']}** (置信度: {match['confidence']}%)\n"
            output += f"   - 功率范围: {match['power_match']}\n"
            output += f"   - 典型特征: {', '.join(match['characteristics'])}\n"
            output += f"   - 使用规律: {match['usage_pattern']}\n\n"
        
        return output
        
    except Exception as e:
        return f"识别设备时出错: {str(e)}"

@tool
def analyze_consumption_tool(analysis_type: str = "full") -> str:
    """
    分析用电统计数据，支持多种分析维度。
    
    参数:
        analysis_type: 分析类型，可选:
            - "daily": 日用电分析
            - "hourly": 小时用电分析  
            - "weekly": 周用电对比
            - "quality": 电能质量分析
            - "full": 综合分析报告 (默认)
    
    返回:
        详细的用电分析报告
    """
    try:
        from tools.data_loader import load_meter_data
        from tools.consumption_analyzer import (
            analyze_daily_consumption,
            analyze_hourly_consumption,
            analyze_weekly_consumption,
            analyze_power_quality,
            generate_consumption_report
        )
        
        # 加载数据
        result = load_meter_data()
        if not result['success']:
            return f"加载数据失败: {result.get('error', '未知错误')}"
        df = result['data']
        
        if analysis_type == "daily":
            daily = analyze_daily_consumption(df)
            output = f"""
📊 日用电量分析

总用电量: {daily['summary']['total_energy']} kWh (共{daily['summary']['total_days']}天)
日均用电: {daily['summary']['avg_daily_energy']} kWh
最高日: {daily['summary']['max_consumption_day']['date']} ({daily['summary']['max_consumption_day']['energy']} kWh)
最低日: {daily['summary']['min_consumption_day']['date']} ({daily['summary']['min_consumption_day']['energy']} kWh)
"""
            return output
            
        elif analysis_type == "hourly":
            hourly = analyze_hourly_consumption(df)
            output = f"""
⏰ 小时用电模式分析

🔴 高峰时段: {', '.join([f'{h}:00' for h in hourly['peak_hours']])}
🟢 低谷时段: {', '.join([f'{h}:00' for h in hourly['valley_hours']])}

用电规律: 高峰时段集中在中午和傍晚，低谷时段在深夜至凌晨
"""
            return output
            
        elif analysis_type == "weekly":
            weekly = analyze_weekly_consumption(df)
            output = f"""
📆 周用电对比分析

工作日平均: {weekly['weekday_comparison']['weekday_avg']} kWh
周末平均: {weekly['weekday_comparison']['weekend_avg']} kWh
差异: {weekly['weekday_comparison']['difference_percent']}%

周末用电量{'高于' if weekly['weekday_comparison']['difference'] > 0 else '低于'}工作日
"""
            return output
            
        elif analysis_type == "quality":
            quality = analyze_power_quality(df)
            output = f"""
⚡ 电能质量分析

电压稳定性: {quality['quality_assessment']['voltage_stability']}
- 平均电压: {quality['voltage']['mean']}V
- 电压波动: {quality['voltage']['std']}V
- 越限比例: {quality['voltage']['out_of_range_percent']}%

功率因数: {quality['quality_assessment']['power_factor']}
- 平均功率因数: {quality['power_factor']['mean']}
- 低功率因数时段: {quality['power_factor']['low_pf_percent']}%
"""
            return output
            
        else:  # full
            report = generate_consumption_report(df)
            return report
            
    except Exception as e:
        return f"分析用电数据时出错: {str(e)}"

@tool
def evaluate_efficiency_tool(appliance_name: str = None) -> str:
    """
    评估能效等级，提供改进建议。
    
    参数:
        appliance_name: 电器名称 (如: 空调、冰箱、热水器等)
                       如果不指定，则评估整体能效
    
    返回:
        能效评估报告和改进建议
    """
    try:
        from tools.data_loader import load_meter_data
        from tools.efficiency_evaluator import (
            calculate_appliance_efficiency,
            evaluate_overall_efficiency,
            compare_efficiency_by_time
        )
        
        # 加载数据
        result = load_meter_data()
        if not result['success']:
            return f"加载数据失败: {result.get('error', '未知错误')}"
        df = result['data']
        
        if appliance_name:
            # 评估单个设备
            eval_result = calculate_appliance_efficiency(df, appliance_name)
            
            if 'error' in eval_result:
                return eval_result['error']
            
            output = f"""
🔧 {appliance_name} 能效评估

能效等级: {eval_result['efficiency_level'].upper()}
能效评分: {eval_result['efficiency_score']}/100
平均功率: {eval_result['avg_power']} W
预估日用电: {eval_result['estimated_daily_usage']} kWh

💡 改进建议:
"""
            for suggestion in eval_result['suggestions']:
                output += f"- {suggestion}\n"
            
            return output
            
        else:
            # 评估整体能效
            overall = evaluate_overall_efficiency(df)
            by_time = compare_efficiency_by_time(df)
            
            output = f"""
🏆 整体能效评估

综合评分: {overall['overall_score']}/100 ({overall['level_description']})

📊 能效指标:
- 能源利用率: {overall['metrics']['energy_utilization']}
- 负载率: {overall['metrics']['load_factor']}
- 基载比: {overall['metrics']['base_load_ratio']}

📈 功率统计:
- 平均功率: {overall['power_stats']['average_power']} W
- 峰值功率: {overall['power_stats']['peak_power']} W
- 基础负载: {overall['power_stats']['base_load']} W

🕐 分时段效率:
- 最佳时段: {by_time['best_period']['name']} (评分: {by_time['best_period']['efficiency_score']})
- 最差时段: {by_time['worst_period']['name']} (评分: {by_time['worst_period']['efficiency_score']})

💡 改进建议:
"""
            for suggestion in overall['improvement_suggestions']:
                output += f"- {suggestion}\n"
            
            for rec in by_time['recommendations']:
                output += f"- {rec}\n"
            
            return output
            
    except Exception as e:
        return f"评估能效时出错: {str(e)}"

@tool
def detect_anomalies_tool(alert_level: str = "all") -> str:
    """
    检测用电异常和潜在故障。
    
    参数:
        alert_level: 告警级别筛选，可选:
            - "all": 显示所有异常 (默认)
            - "high": 仅显示高优先级告警
            - "summary": 仅显示概要
    
    返回:
        异常检测报告和告警信息
    """
    try:
        from tools.data_loader import load_meter_data
        from tools.anomaly_detector import (
            detect_voltage_anomalies,
            detect_power_anomalies,
            detect_consumption_anomalies,
            generate_anomaly_alert_report
        )
        
        # 加载数据
        result = load_meter_data()
        if not result['success']:
            return f"加载数据失败: {result.get('error', '未知错误')}"
        df = result['data']
        
        # 生成综合告警报告
        report = generate_anomaly_alert_report(df)
        
        if alert_level == "summary":
            return f"""
🚨 异常检测概要

告警级别: {report['alert_level_description']}
总体状态: {report['summary_message']}

统计:
- 高优先级异常: {report['statistics']['high_priority']} 项
- 中优先级异常: {report['statistics']['medium_priority']} 项
- 电压异常: {report['statistics']['voltage_anomalies']} 项
- 功率异常: {report['statistics']['power_anomalies']} 项
- 用电异常: {report['statistics']['consumption_anomalies']} 项
"""
        
        elif alert_level == "high":
            high_priority = [a for a in report['detailed_anomalies'] if a.get('severity') == 'high']
            if not high_priority:
                return "✅ 未检测到高优先级异常"
            
            output = f"""
🚨 高优先级异常告警

告警级别: {report['alert_level_description']}
"""
            for i, anomaly in enumerate(high_priority, 1):
                output += f"\n{i}. [{anomaly['type']}] {anomaly['description']}\n"
                output += f"   - 异常数量: {anomaly['count']} ({anomaly['percentage']}%)\n"
                if 'possible_causes' in anomaly:
                    output += f"   - 可能原因: {', '.join(anomaly['possible_causes'])}\n"
                if 'recommendation' in anomaly:
                    output += f"   - 处理建议: {anomaly['recommendation']}\n"
            
            return output
        
        else:  # all
            output = f"""
🚨 综合异常检测报告

告警级别: {report['alert_level_description']}
总体状态: {report['summary_message']}

{'='*60}

📊 异常统计:
- 总异常数: {report['statistics']['total_anomalies']}
- 🔴 高优先级: {report['statistics']['high_priority']} 项
- 🟡 中优先级: {report['statistics']['medium_priority']} 项

⚡ 分类统计:
- 电压异常: {report['statistics']['voltage_anomalies']} 项 [{report['voltage_status']}]
- 功率异常: {report['statistics']['power_anomalies']} 项 [{report['power_status']}]
- 用电异常: {report['statistics']['consumption_anomalies']} 项 [{report['consumption_status']}]

{'='*60}

📋 详细异常列表:
"""
            if not report['detailed_anomalies']:
                output += "\n未检测到明显异常\n"
            else:
                for i, anomaly in enumerate(report['detailed_anomalies'], 1):
                    severity_icon = "🔴" if anomaly.get('severity') == 'high' else "🟡"
                    output += f"\n{i}. {severity_icon} [{anomaly['type']}] {anomaly['description']}\n"
                    output += f"   - 异常数量: {anomaly['count']} ({anomaly['percentage']}%)\n"
                    if 'possible_causes' in anomaly:
                        output += f"   - 可能原因: {', '.join(anomaly['possible_causes'])}\n"
                    if 'recommendation' in anomaly:
                        output += f"   - 处理建议: {anomaly['recommendation']}\n"
            
            if report['recommended_actions']:
                output += f"\n{'='*60}\n\n📝 推荐处理措施:\n"
                for action in report['recommended_actions']:
                    output += f"- {action}\n"
            
            return output
            
    except Exception as e:
        return f"检测异常时出错: {str(e)}"

@tool
def generate_charts_tool(chart_type: str = "all") -> str:
    """
    生成可视化图表。
    
    参数:
        chart_type: 图表类型，可选:
            - "all": 生成所有图表 (默认)
            - "trend": 功率趋势图
            - "daily": 日用电量图
            - "hourly": 小时用电模式图
            - "quality": 电能质量图
            - "efficiency": 能效仪表盘
    
    返回:
        生成的图表文件路径
    """
    try:
        from tools.data_loader import load_meter_data
        from tools.chart_generator import (
            generate_power_trend_chart,
            generate_daily_consumption_chart,
            generate_hourly_pattern_chart,
            generate_power_quality_chart,
            generate_efficiency_gauge,
            generate_comprehensive_report
        )
        from tools.efficiency_evaluator import evaluate_overall_efficiency
        
        # 加载数据
        result = load_meter_data()
        if not result['success']:
            return f"加载数据失败: {result.get('error', '未知错误')}"
        df = result['data']
        
        # 评估整体能效获取分数
        overall = evaluate_overall_efficiency(df)
        efficiency_score = overall['overall_score']
        
        charts = []
        
        if chart_type == "all":
            charts = generate_comprehensive_report(df, efficiency_score)
        elif chart_type == "trend":
            charts.append(generate_power_trend_chart(df.tail(24*60)))
        elif chart_type == "daily":
            charts.append(generate_daily_consumption_chart(df))
        elif chart_type == "hourly":
            charts.append(generate_hourly_pattern_chart(df))
        elif chart_type == "quality":
            charts.append(generate_power_quality_chart(df))
        elif chart_type == "efficiency":
            charts.append(generate_efficiency_gauge(efficiency_score, 'Overall Efficiency'))
        
        if not charts:
            return "未生成任何图表"
        
        output = f"""
📊 可视化图表已生成！

共生成 {len(charts)} 张图表:

"""
        for i, chart_path in enumerate(charts, 1):
            chart_name = os.path.basename(chart_path)
            output += f"{i}. `{chart_name}`\n"
            output += f"   路径: {chart_path}\n\n"
        
        output += "\n图表文件保存在: `/workspace/projects/assets/charts/`"
        
        return output
        
    except Exception as e:
        return f"生成图表时出错: {str(e)}"

@tool
def help_tool() -> str:
    """
    显示智能电表能效分析Agent的使用帮助。
    
    返回:
        详细的使用说明
    """
    return """
🤖 智能电表能效分析Agent - 使用帮助

您好！我是您的智能电表能效分析助手。我可以帮助您：

📊 【用电分析】
- 分析日/周/月的用电量统计
- 识别用电高峰和低谷时段
- 评估电能质量（电压、功率因数等）

🔌 【设备识别】
- 根据功率特征识别家用电器
- 分析各类设备用电占比

⚡ 【能效评估】
- 评估单个设备或整体能效等级
- 提供节能改进建议
- 对比不同时段的能效表现

🚨 【异常检测】
- 检测电压异常（过压、欠压、暂降、暂升）
- 识别功率突变和异常用电
- 生成综合告警报告

📈 【图表生成】
- 生成功率趋势图
- 日用电量柱状图
- 小时用电模式图
- 电能质量分析图
- 能效仪表盘

━━━━━━━━━━━━━━━━━━━━━━━━━━━

💡 使用示例：

1. "加载电表数据" - 加载并查看数据概览
2. "分析日用电量" - 查看每日用电统计
3. "识别这个800W的设备" - 识别设备类型
4. "评估空调的能效" - 评估特定设备
5. "检测异常" - 检查用电异常
6. "生成所有图表" - 创建可视化报告

请告诉我您想了解什么！
"""

def build_agent(ctx=None):
    """
    构建智能电表能效分析Agent
    
    参数:
        ctx: 请求上下文（可选）
    
    返回:
        配置好的Agent实例
    """
    # 读取配置
    workspace_path = os.getenv("COZE_WORKSPACE_PATH", "/workspace/projects")
    config_path = os.path.join(workspace_path, LLM_CONFIG)
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            cfg = json.load(f)
    except Exception:
        # 默认配置
        cfg = {
            "config": {
                "model": "doubao-seed-2.0-lite-250120",
                "temperature": 0.7,
                "top_p": 0.9,
                "max_completion_tokens": 8000,
                "timeout": 600,
                "thinking": "disabled"
            },
            "sp": "You are a helpful assistant for smart meter energy efficiency analysis.",
            "tools": []
        }
    
    # 获取API配置
    api_key = os.getenv("COZE_WORKLOAD_IDENTITY_API_KEY")
    base_url = os.getenv("COZE_INTEGRATION_MODEL_BASE_URL")
    
    # 创建LLM
    llm = ChatOpenAI(
        model=cfg['config'].get("model"),
        api_key=api_key,
        base_url=base_url,
        temperature=cfg['config'].get('temperature', 0.7),
        streaming=True,
        timeout=cfg['config'].get('timeout', 600),
        extra_body={
            "thinking": {
                "type": cfg['config'].get('thinking', 'disabled')
            }
        }
    )
    
    # 定义工具列表
    tools = [
        load_meter_data_tool,
        identify_appliance_tool,
        analyze_consumption_tool,
        evaluate_efficiency_tool,
        detect_anomalies_tool,
        generate_charts_tool,
        help_tool
    ]
    
    # 系统提示词
    system_prompt = """# 角色定义
你是智能电表能效分析专家，专注于家庭和工业用电数据的分析、诊断和优化建议。

# 核心能力
- 加载和分析智能电表数据
- 基于功率特征识别家用电器类型
- 用电统计分析和趋势预测
- 设备能效评估和节能建议
- 用电异常检测和告警
- 生成可视化图表报告

# 分析范围
支持的电器识别：空调、冰箱、热水器、洗衣机、照明、电视、微波炉、电磁炉、电饭煲、电暖器等

# 分析维度
1. 时间维度：分钟级、小时级、日级、周级、月级
2. 指标维度：功率、电压、电流、电能、功率因数
3. 异常维度：电压异常、功率异常、用电模式异常

# 输出规范
- 数据分析结果用清晰的Markdown格式呈现
- 异常告警要标注严重程度（🔴高 🟡中 🟢低）
- 建议要具体、可执行
- 图表路径使用标准文件路径格式

# 约束
- 只分析智能电表相关数据
- 不编造数据或分析结果
- 如数据不足或分析失败，明确告知用户
"""
    
    # 创建Agent
    agent = create_agent(
        model=llm,
        system_prompt=system_prompt,
        tools=tools,
        checkpointer=None,  # 如需记忆能力可启用
        state_schema=AgentState,
    )
    
    return agent

# 导出Agent类（兼容旧接口）
Agent = type('Agent', (), {'build': build_agent})
