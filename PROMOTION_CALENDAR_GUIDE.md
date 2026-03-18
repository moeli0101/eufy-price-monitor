# 📅 促销日历系统 - 使用指南

## 🎯 功能概述

促销日历系统可以帮助你：
- 📊 查看每个产品每天的价格和促销状态
- 🔥 对比 eufy 和竞品的促销策略
- 📈 分析促销重叠和独家促销期
- 📄 导出文本报告分享给团队
- 📅 按年份、季度、月份筛选数据

---

## 📁 系统文件说明

### 数据文件（自动生成）
- **price_history.json** - 所有产品的完整价格历史
- **promotions.json** - 促销活动记录（活跃和历史）
- **promotion_calendar.json** - 月度促销日历数据

### 核心模块
- **price_history_manager.py** - 历史价格数据管理
- **promotion_detector.py** - 促销检测和记录
- **promotion_calendar_generator.py** - 日历生成和导出

### Dashboard 页面
- **promotion_calendar.html** - 促销日历可视化界面

---

## 🚀 使用方式

### 1. 在线 Dashboard（推荐）

访问地址（GitHub Actions 运行完成后自动更新）：
```
https://moeli0101.github.io/eufy-price-monitor/promotion_calendar.html
```

**功能**：
- ✅ 选择年份和月份查看促销日历
- ✅ 按品牌、品类筛选产品
- ✅ 搜索特定产品名称
- ✅ 勾选多个产品进行对比
- ✅ 查看促销统计数据
- ✅ 一键导出文本报告

---

### 2. 本地使用

#### 方法 A：查看 Dashboard
```bash
cd /Users/anker/Desktop/feishu_bot
open promotion_calendar.html
```

#### 方法 B：生成文本报告
```bash
python3 -c "
from promotion_calendar_generator import PromotionCalendarGenerator
from datetime import datetime

# 初始化生成器
generator = PromotionCalendarGenerator()

# 生成当月日历
now = datetime.now()
calendar = generator.generate_monthly_calendar(now.year, now.month)

# 导出文本
generator.export_text_format(calendar)

print('✅ 文本报告已生成：promotion_calendar.txt')
"
```

#### 方法 C：对比分析
```python
from promotion_calendar_generator import PromotionCalendarGenerator

generator = PromotionCalendarGenerator()

# 选择要对比的产品
product_ids = [
    'eufy_eufycam_s330',
    'ring_stick_up_cam_pro'
]

# 生成对比报告
comparison = generator.generate_comparison_view(
    product_ids=product_ids,
    start_date='2026-03-01',
    end_date='2026-03-31'
)

# 导出对比文本
generator.export_comparison_text(comparison)
```

---

## 📊 Dashboard 功能详解

### 1. 筛选器

**年份选择**
- 查看历史年份的促销数据
- 默认显示当前年份

**月份选择**
- 选择1-12月查看具体月份
- 默认显示当前月份

**品牌筛选**
- 所有品牌
- eufy
- Ring
- Arlo
- Google Nest
- TP-Link
- Swann
- Yale
- 其他

**品类筛选**
- 所有品类
- Security Camera（安防摄像头）
- Video Doorbell（视频门铃）
- Smart Lock（智能门锁）

**产品搜索**
- 输入产品名称快速筛选
- 实时搜索，即时显示结果

---

### 2. 产品选择器

- ✅ 勾选产品将其添加到日历对比
- ✅ 支持多选，无数量限制
- ✅ 显示产品名称和品牌
- ✅ 根据筛选器自动更新列表

---

### 3. 日历表格

**表格结构**：
- 第一列：产品名称（固定列）
- 后续列：该月每一天（1-31日）

**单元格显示**：
- **正常价格**：白色背景，显示价格
- **促销价格**：黄色背景，显示折扣标签
- **无数据**：灰色背景，显示 "-"

**示例**：
```
产品           1日    2日    3日    4日    5日
────────────────────────────────────────────
eufy S330    $299   $299   $249   $249   $199
                            17%    17%    33%
                            OFF    OFF    OFF

Ring Cam     $179   $149   $149   $179   $179
                     17%    17%
                     OFF    OFF
```

---

### 4. 统计面板

自动计算并显示：
- **选中产品数**：当前对比的产品总数
- **总促销天数**：所有产品的促销天数总和
- **平均折扣**：所有促销的平均折扣百分比

---

### 5. 导出文本

点击"导出文本"按钮，生成包含以下内容的 `.txt` 文件：

```
促销日历导出
时间：2026年3月
================================================================================

产品：eufyCam S330 (eufy)
品类：Security Camera
────────────────────────────────────────────────────────────────────────────────
  2026-03-01: $299 - 正常价格
  2026-03-02: $299 - 正常价格
  2026-03-03: $249 - 🔥 促销 (17% OFF)
  2026-03-04: $249 - 🔥 促销 (17% OFF)
  2026-03-05: $199 - 🔥 促销 (33% OFF)
  ...
```

---

## 🔍 使用场景

### 场景 1：查看 eufy 产品促销规律
1. 品牌筛选选择 "eufy"
2. 勾选你关心的 eufy 产品
3. 切换不同月份，观察促销周期
4. 导出报告给团队

### 场景 2：对比 eufy vs 竞品
1. 勾选 eufy S330
2. 勾选 Ring Stick Up Cam
3. 勾选 Arlo Ultra
4. 查看日历表格，对比促销时间
5. 分析促销重叠和独家促销期

### 场景 3：分析竞品促销策略
1. 品牌筛选选择 "Ring" 或其他竞品
2. 勾选该品牌的多个产品
3. 观察促销频率和折扣力度
4. 发现促销规律（节假日、季度末等）

### 场景 4：季度促销分析
1. 年份选择 "2026"
2. 依次查看 1月、2月、3月
3. 记录每个月的促销情况
4. 生成季度报告

---

## 📈 数据更新

### 自动更新
- ⏰ 每天 UTC 18:00（澳洲东部时间凌晨2-4点）自动运行
- ✅ 自动抓取最新价格
- ✅ 自动检测促销变化
- ✅ 自动生成日历数据
- ✅ 自动提交到 GitHub

### 手动触发
访问：https://github.com/moeli0101/eufy-price-monitor/actions
点击 "Run workflow" 手动触发更新

---

## 🎯 高级功能

### 1. 促销检测规则

系统自动检测促销的条件：
- ✅ 当前价格 < 原价
- ✅ 折扣 ≥ 5%
- ✅ 自动记录促销开始日期
- ✅ 自动记录促销结束日期
- ✅ 计算促销持续天数

### 2. 产品 ID 生成规则

系统为每个产品生成唯一 ID：
- 格式：`{brand}_{product_name}`
- 转小写，移除特殊字符
- 示例：`eufy_eufycam_s330`

### 3. 历史数据保留

- 📁 **price_history.json** - 永久保留所有历史
- 📁 **promotions.json** - 活跃促销 + 历史促销
- 📁 **promotion_calendar.json** - 当月数据（每月更新）

---

## 🐛 故障排除

### 问题 1：Dashboard 显示"加载数据失败"
**原因**：price_history.json 文件不存在或格式错误

**解决**：
```bash
# 检查文件是否存在
ls -lh price_history.json

# 重新运行抓取脚本生成数据
python3 daily_price_refresh.py
```

### 问题 2：某些产品没有历史数据
**原因**：该产品是新添加的，还没有累积足够的历史

**解决**：等待系统每天自动运行，数据会逐渐累积

### 问题 3：促销没有被检测到
**原因**：折扣小于5%，或者价格数据有问题

**解决**：
```bash
# 检查 promotions.json
cat promotions.json | python3 -m json.tool

# 手动运行促销检测
python3 -c "
from promotion_detector import PromotionDetector
detector = PromotionDetector()
stats = detector.get_statistics()
print(stats)
"
```

---

## 💡 使用技巧

1. **定期导出报告**：每周导出一次，跟踪促销趋势
2. **对比同类产品**：勾选同品类产品，发现价格优势
3. **节假日分析**：查看节假日期间的促销活动
4. **季度复盘**：每个季度末回顾促销策略效果

---

## 📞 支持

如有问题，请查看：
- 📄 **daily_price_refresh.py** - 抓取脚本主逻辑
- 📄 **price_history_manager.py** - 历史数据管理
- 📄 **promotion_detector.py** - 促销检测逻辑
- 📄 **promotion_calendar_generator.py** - 日历生成逻辑

---

**🎉 开始使用促销日历，优化你的定价策略！**
