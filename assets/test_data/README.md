# 智能电表能效分析Agent - 测试用例说明

## 📁 测试数据位置

```
/workspace/projects/assets/test_data/
├── README.md                           # 数据集说明
├── scenario_1_typical_day.csv          # 场景1：典型家庭日用电
├── scenario_2_with_anomalies.csv        # 场景2：包含异常的用电数据
├── scenario_3_weekend.csv               # 场景3：周末高用电
├── scenario_4_air_conditioner.csv       # 场景4：空调运行数据
├── scenario_5_power_quality.csv        # 场景5：电能质量问题数据
```

## 🧪 测试套件

运行完整测试套件：
```bash
python tests/test_suite.py
```

## 📊 各测试场景说明

### 场景1：典型家庭日用电 (scenario_1_typical_day.csv)
- **记录数**：1440条（24小时×60分钟）
- **总电量**：约9.55 kWh
- **平均功率**：398 W
- **用途**：
  - 验证日用电分析功能
  - 验证小时用电模式识别
  - 验证峰谷时段检测

### 场景2：包含异常的用电数据 (scenario_2_with_anomalies.csv)
- **记录数**：1440条
- **注入的异常**：
  - 10:30 - 电压尖峰 (280V+)
  - 14:15 - 功率突增 (2500W+)
  - 18:45 - 功率突降 (<100W)
  - 22:00 - 电压暂降 (<190V)
- **用途**：
  - 验证电压异常检测
  - 验证功率突变检测
  - 验证告警分级功能

### 场景3：周末高用电 (scenario_3_weekend.csv)
- **记录数**：1440条
- **总电量**：约18.89 kWh
- **平均功率**：787 W
- **用电特点**：
  - 8:00-12:00 洗衣机运行
  - 18:00-22:00 晚餐+电视高峰
- **用途**：
  - 验证周用电对比功能
  - 验证工作日vs周末分析

### 场景4：空调运行数据 (scenario_4_air_conditioner.csv)
- **记录数**：1440条
- **总电量**：约21.44 kWh
- **平均功率**：893 W
- **设备特点**：
  - 模拟空调周期性启停
  - 功率范围：100-1300W
- **用途**：
  - 验证设备识别功能
  - 验证高功率设备分析

### 场景5：电能质量问题数据 (scenario_5_power_quality.csv)
- **记录数**：1440条
- **注入的问题**：
  - 8:00-10:00 电压偏低 (205V左右)
  - 14:00-16:00 电压偏高 (235V左右)
  - 18:00-20:00 功率因数低 (<0.87)
- **用途**：
  - 验证电能质量分析
  - 验证功率因数检测

## 🔧 使用示例

### 加载特定测试数据
```python
from tools.data_loader import load_meter_data

# 加载场景2的异常数据
result = load_meter_data('/workspace/projects/assets/test_data/scenario_2_with_anomalies.csv')
df = result['data']
```

### 运行特定测试
```python
import sys
sys.path.insert(0, '/workspace/projects/src')
from tests.test_suite import test_case_3

# 运行异常检测测试
test_case_3()
```

### 验证图表生成
```python
from tools.chart_generator import generate_daily_consumption_chart

# 为特定场景生成图表
chart_path = generate_daily_consumption_chart(df)
print(f"图表已生成: {chart_path}")
```

## 📈 预期测试结果

| 测试用例 | 状态 | 说明 |
|---------|------|------|
| 设备识别 | ✓ | 功率匹配功能正常 |
| 日用电分析 | ✓ | 日用电统计正确 |
| 异常检测 | ✓ | 成功检测到注入的异常 |
| 周用电对比 | ✓ | 周末高用电特征明显 |
| 电能质量分析 | ✓ | 电压异常检测成功 |
| 图表生成 | ✓ | 图表生成功能正常 |
| 能效评估 | ✓ | 评分计算正确 |
| 完整数据测试 | ✓ | 43200条数据处理正常 |

## 🎯 测试覆盖率

- ✅ 数据加载功能
- ✅ 设备识别功能
- ✅ 用电统计分析（日/小时/周）
- ✅ 能效评估功能
- ✅ 异常检测功能（电压/功率/用电模式）
- ✅ 图表生成功能
- ✅ 电能质量分析
- ✅ 大数据量处理（43200条记录）

## 📝 添加新测试数据

如需添加新的测试场景，按以下步骤：

1. 创建CSV文件，包含以下字段：
```csv
timestamp,voltage,current,active_power,reactive_power,power_factor,energy
2024-03-15 00:00:00,220.5,1.5,330.0,99.0,0.958,0.0055
```

2. 将文件保存到 `/workspace/projects/assets/test_data/`

3. 在 `generate_test_data.py` 中添加新的生成函数

4. 在 `test_suite.py` 中添加新的测试用例
