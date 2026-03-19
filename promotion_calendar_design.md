# 促销日历系统实现方案

## 📋 需求分析

### 核心功能
1. ✅ 每天自动爬取价格数据
2. ✅ 记录历史价格和促销信息
3. ✅ Dashboard可视化展示
4. ✅ 多产品对比
5. ✅ 时间维度筛选（年/季度/月）
6. ✅ 产品维度筛选（SKU/品牌/产品名）
7. ✅ 导出文本版

---

## 🏗️ 系统架构

```
GitHub Actions (每天凌晨2点)
         ↓
daily_price_refresh.py (抓取最新价格)
         ↓
price_history_manager.py (管理历史数据)
         ↓
promotion_detector.py (检测促销)
         ↓
JSON数据存储
         ├─ price_history.json (完整历史)
         ├─ promotions.json (促销记录)
         └─ price_results_latest.json (最新价格)
         ↓
Dashboard可视化
         ├─ 价格趋势图
         ├─ 促销日历
         └─ 对比分析
```

---

## 📁 数据结构设计

### 1. price_history.json (完整历史)

```json
{
  "eufy_S330": {
    "product_name": "eufyCam S330",
    "brand": "eufy",
    "category": "Security Camera",
    "price_history": [
      {
        "date": "2026-03-01",
        "price": 299,
        "original_price": 299,
        "is_on_sale": false,
        "discount_percentage": 0,
        "sale_badge": null
      },
      {
        "date": "2026-03-15",
        "price": 249,
        "original_price": 299,
        "is_on_sale": true,
        "discount_percentage": 17,
        "sale_badge": "17% OFF"
      },
      {
        "date": "2026-03-18",
        "price": 199,
        "original_price": 299,
        "is_on_sale": true,
        "discount_percentage": 33,
        "sale_badge": "33% OFF"
      }
    ]
  },
  "ring_stick_up_cam": {
    "product_name": "Ring Stick Up Cam Pro",
    "brand": "Ring",
    "category": "Security Camera",
    "price_history": [...]
  }
}
```

### 2. promotions.json (促销记录)

```json
{
  "active_promotions": [
    {
      "product_id": "eufy_S330",
      "product_name": "eufyCam S330",
      "start_date": "2026-03-15",
      "end_date": null,
      "original_price": 299,
      "sale_price": 199,
      "discount_percentage": 33,
      "duration_days": 3,
      "status": "active"
    }
  ],
  "historical_promotions": [
    {
      "product_id": "eufy_S330",
      "start_date": "2026-02-14",
      "end_date": "2026-02-20",
      "original_price": 299,
      "sale_price": 249,
      "discount_percentage": 17,
      "duration_days": 6,
      "status": "ended"
    }
  ]
}
```

### 3. promotion_calendar.json (日历视图数据)

```json
{
  "2026-03": {
    "eufy_S330": {
      "1": {"price": 299, "is_sale": false},
      "2": {"price": 299, "is_sale": false},
      "15": {"price": 249, "is_sale": true, "discount": 17},
      "18": {"price": 199, "is_sale": true, "discount": 33}
    },
    "ring_stick_up_cam": {
      "1": {"price": 179, "is_sale": false},
      "10": {"price": 149, "is_sale": true, "discount": 17}
    }
  }
}
```

---

## 💻 核心代码模块

### 模块1：price_history_manager.py

```python
import json
from datetime import datetime
from pathlib import Path

class PriceHistoryManager:
    def __init__(self):
        self.history_file = "price_history.json"
        self.load_history()

    def load_history(self):
        """加载历史数据"""
        if Path(self.history_file).exists():
            with open(self.history_file, 'r', encoding='utf-8') as f:
                self.history = json.load(f)
        else:
            self.history = {}

    def update_price(self, product_id, product_data):
        """更新产品价格"""
        today = datetime.now().strftime("%Y-%m-%d")

        if product_id not in self.history:
            self.history[product_id] = {
                "product_name": product_data["name"],
                "brand": product_data["brand"],
                "category": product_data["category"],
                "price_history": []
            }

        # 检查今天是否已有记录
        history = self.history[product_id]["price_history"]
        if not history or history[-1]["date"] != today:
            price_record = {
                "date": today,
                "price": product_data["current_price"],
                "original_price": product_data.get("original_price", product_data["current_price"]),
                "is_on_sale": product_data.get("is_on_sale", False),
                "discount_percentage": product_data.get("discount_percentage", 0),
                "sale_badge": product_data.get("sale_badge")
            }
            history.append(price_record)

    def save_history(self):
        """保存历史数据"""
        with open(self.history_file, 'w', encoding='utf-8') as f:
            json.dump(self.history, f, indent=2, ensure_ascii=False)

    def get_price_range(self, product_id, start_date, end_date):
        """获取指定时间段的价格"""
        if product_id not in self.history:
            return []

        history = self.history[product_id]["price_history"]
        return [
            record for record in history
            if start_date <= record["date"] <= end_date
        ]
```

### 模块2：promotion_detector.py

```python
class PromotionDetector:
    def __init__(self):
        self.promotions_file = "promotions.json"
        self.load_promotions()

    def detect_promotion(self, product_id, current_price, original_price):
        """检测是否是促销"""
        discount = ((original_price - current_price) / original_price) * 100

        # 折扣大于10%认为是促销
        if discount >= 10:
            return {
                "is_promotion": True,
                "discount_percentage": round(discount),
                "save_amount": original_price - current_price
            }
        return {"is_promotion": False}

    def update_promotions(self, product_id, product_data, promotion_info):
        """更新促销记录"""
        today = datetime.now().strftime("%Y-%m-%d")

        if promotion_info["is_promotion"]:
            # 检查是否有活跃的促销
            active = self.get_active_promotion(product_id)
            if not active:
                # 新促销开始
                self.promotions["active_promotions"].append({
                    "product_id": product_id,
                    "product_name": product_data["name"],
                    "start_date": today,
                    "end_date": None,
                    "original_price": product_data["original_price"],
                    "sale_price": product_data["current_price"],
                    "discount_percentage": promotion_info["discount_percentage"],
                    "duration_days": 1,
                    "status": "active"
                })
            else:
                # 更新促销天数
                active["duration_days"] += 1
                active["sale_price"] = product_data["current_price"]
        else:
            # 促销结束
            active = self.get_active_promotion(product_id)
            if active:
                active["end_date"] = today
                active["status"] = "ended"
                self.promotions["historical_promotions"].append(active)
                self.promotions["active_promotions"].remove(active)

    def get_promotion_calendar(self, year, month):
        """生成促销日历"""
        # 从历史数据生成月度日历视图
        pass
```

### 模块3：promotion_calendar_generator.py

```python
class PromotionCalendarGenerator:
    def generate_monthly_calendar(self, year, month, product_ids=None):
        """生成月度促销日历"""
        calendar_data = {}

        for product_id in product_ids or self.get_all_products():
            price_history = self.get_monthly_prices(product_id, year, month)
            calendar_data[product_id] = self.format_calendar_row(price_history)

        return calendar_data

    def generate_comparison_view(self, product_ids, start_date, end_date):
        """生成对比视图"""
        comparison = {
            "products": [],
            "overlap_analysis": {}
        }

        for product_id in product_ids:
            prices = self.get_price_range(product_id, start_date, end_date)
            promotions = self.get_promotions(product_id, start_date, end_date)

            comparison["products"].append({
                "id": product_id,
                "prices": prices,
                "promotions": promotions,
                "avg_discount": self.calculate_avg_discount(promotions)
            })

        # 分析促销重叠
        comparison["overlap_analysis"] = self.analyze_overlap(product_ids, start_date, end_date)

        return comparison

    def export_text_format(self, calendar_data):
        """导出文本格式"""
        output = []
        output.append("促销日历导出")
        output.append("=" * 80)
        output.append("")

        for product_id, days in calendar_data.items():
            output.append(f"产品：{product_id}")
            output.append("-" * 80)

            for day, data in days.items():
                status = "🔥促销" if data["is_sale"] else "正常"
                output.append(f"  {day}日: ${data['price']} ({status})")

            output.append("")

        return "\n".join(output)
```

---

## 🎨 Dashboard可视化设计

### 新增页面：promotion_calendar.html

#### 1. 日历视图

```html
<div class="calendar-container">
  <!-- 筛选器 -->
  <div class="filters">
    <select id="year-select">
      <option>2026</option>
      <option>2025</option>
    </select>

    <select id="month-select">
      <option>3月</option>
      <option>2月</option>
      <option>1月</option>
    </select>

    <select id="brand-filter">
      <option value="all">所有品牌</option>
      <option value="eufy">eufy</option>
      <option value="Ring">Ring</option>
      <option value="Arlo">Arlo</option>
    </select>

    <button id="compare-btn">对比选中产品</button>
    <button id="export-btn">导出文本</button>
  </div>

  <!-- 产品选择 -->
  <div class="product-selector">
    <label><input type="checkbox" data-product="eufy_S330"> eufy S330</label>
    <label><input type="checkbox" data-product="ring_cam"> Ring Cam</label>
    <label><input type="checkbox" data-product="arlo_ultra"> Arlo Ultra</label>
  </div>

  <!-- 日历表格 -->
  <table class="calendar-table">
    <thead>
      <tr>
        <th>产品</th>
        <th>1</th><th>2</th><th>3</th>...<th>31</th>
      </tr>
    </thead>
    <tbody id="calendar-body">
      <!-- 动态生成 -->
    </tbody>
  </table>
</div>
```

#### 2. 趋势对比图

```html
<div class="comparison-view">
  <canvas id="price-trend-chart"></canvas>

  <div class="promotion-overlap">
    <h3>促销重叠分析</h3>
    <div class="overlap-stats">
      <p>同时促销天数：5天</p>
      <p>eufy优势期：8天</p>
      <p>Ring优势期：12天</p>
    </div>
  </div>
</div>
```

#### 3. JavaScript交互

```javascript
class PromotionCalendar {
  constructor() {
    this.selectedProducts = [];
    this.currentYear = 2026;
    this.currentMonth = 3;
  }

  async loadCalendar() {
    const data = await fetch('promotion_calendar.json');
    const calendar = await data.json();
    this.renderCalendar(calendar);
  }

  renderCalendar(data) {
    const tbody = document.getElementById('calendar-body');
    tbody.innerHTML = '';

    for (const [productId, days] of Object.entries(data)) {
      const row = document.createElement('tr');
      row.innerHTML = `<td>${productId}</td>`;

      for (let day = 1; day <= 31; day++) {
        const dayData = days[day];
        const cell = document.createElement('td');

        if (dayData) {
          cell.className = dayData.is_sale ? 'sale-day' : 'normal-day';
          cell.innerHTML = `
            <div class="price-cell">
              <span class="price">$${dayData.price}</span>
              ${dayData.is_sale ? `<span class="badge">${dayData.discount}% OFF</span>` : ''}
            </div>
          `;
          cell.title = `${dayData.is_sale ? '促销' : '正常'} - $${dayData.price}`;
        } else {
          cell.className = 'no-data';
          cell.innerHTML = '-';
        }

        row.appendChild(cell);
      }

      tbody.appendChild(row);
    }
  }

  compareProducts() {
    const selected = this.getSelectedProducts();
    if (selected.length < 2) {
      alert('请至少选择2个产品进行对比');
      return;
    }

    this.renderComparison(selected);
  }

  exportText() {
    const calendar = this.getCurrentCalendarData();
    const text = this.formatAsText(calendar);

    // 下载文本文件
    const blob = new Blob([text], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `promotion_calendar_${this.currentYear}_${this.currentMonth}.txt`;
    a.click();
  }
}
```

---

## 📊 数据流程

### 每日自动更新流程

```
1. GitHub Actions 触发 (凌晨2点)
   ↓
2. daily_price_refresh.py 抓取最新价格
   ↓
3. PriceHistoryManager 更新历史记录
   ↓
4. PromotionDetector 检测促销变化
   ↓
5. 生成以下文件：
   • price_history.json (追加今日数据)
   • promotions.json (更新促销状态)
   • promotion_calendar.json (生成日历数据)
   ↓
6. 提交到GitHub
   ↓
7. GitHub Pages 自动更新网站
```

---

## 🎯 功能实现优先级

### Phase 1: 基础数据收集 (1-2天)
- ✅ 修改 daily_price_refresh.py 保存历史数据
- ✅ 创建 PriceHistoryManager
- ✅ 每日累积价格数据

### Phase 2: 促销检测 (1天)
- ✅ 创建 PromotionDetector
- ✅ 识别促销开始/结束
- ✅ 生成 promotions.json

### Phase 3: 日历生成 (1天)
- ✅ 创建 PromotionCalendarGenerator
- ✅ 生成月度日历数据
- ✅ 文本导出功能

### Phase 4: Dashboard可视化 (2-3天)
- ✅ 创建日历视图页面
- ✅ 产品选择和筛选
- ✅ 趋势对比图表
- ✅ 交互功能（对比、导出）

---

## 📈 预期效果

### 日历视图示例

```
2026年3月促销日历 - eufy vs 竞品
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

产品              1  2  3  4  5  6  7  8  9 10 11 12 13 14 15
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
eufy S330        ●  ●  ●  ●  ●  ●  ●  ●  ●  ●  ●  ●  ●  ● 🔥
Ring Cam         ●  ●  ●  ●  ●  🔥 🔥 🔥 🔥 🔥 ●  ●  ●  ●  ●
Arlo Ultra       🔥 🔥 🔥 ●  ●  ●  ●  ●  ●  ●  🔥 🔥 🔥 🔥 🔥
Swann Doorbell   ●  ●  ●  ●  ●  ●  ●  ●  ●  ●  ●  ●  ●  ●  ●

图例：● 正常价格  🔥 促销中

促销统计：
• eufy S330: 1次促销，持续1天，平均折扣17%
• Ring Cam: 1次促销，持续5天，平均折扣17%
• Arlo Ultra: 2次促销，持续8天，平均折扣20%
```

### 对比分析示例

```
eufy S330 vs Ring Cam 促销对比 (2026年Q1)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

促销频率：
  eufy S330: 3次 (每月1次)
  Ring Cam:  5次 (每2周1次)

平均折扣：
  eufy S330: 18%
  Ring Cam:  15%

促销重叠：
  同时促销天数: 5天
  eufy独家促销: 12天
  Ring独家促销: 18天

价格优势：
  eufy更便宜: 15天 (最大差距$50)
  Ring更便宜: 20天 (最大差距$30)
```

---

## 🚀 开始实现

现在可以开始实现了！建议使用 Vibe Coding 方式：

1. **告诉我**: "开始搭建促销日历系统"
2. **我会**:
   - 创建所有必要的Python模块
   - 修改现有的抓取脚本
   - 创建新的Dashboard页面
   - 配置自动化流程

3. **你可以随时说**:
   - "日历太复杂了" → 简化设计
   - "对比功能不够直观" → 重新设计UI
   - "我想要更多筛选选项" → 添加功能

预计开发时间：**6-8小时** (使用Vibe Coding)

---

## ✨ 总结

这个促销日历系统将让你：
1. ✅ 一目了然看到所有产品的促销周期
2. ✅ 快速对比eufy和竞品的促销策略
3. ✅ 导出报告给团队使用
4. ✅ 发现竞品促销规律（节假日、季度末等）
5. ✅ 制定更好的定价和促销策略

**完全自动化，零维护！** 🎉
