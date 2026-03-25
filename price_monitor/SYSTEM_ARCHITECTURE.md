# eufy Price Monitor - 系统架构文档

> 最后更新: 2026-03-25
> 版本: 2.0 (支持多品牌母婴产品)

## 📋 目录
- [系统概述](#系统概述)
- [文件结构](#文件结构)
- [核心功能流程](#核心功能流程)
- [产品分类系统](#产品分类系统)
- [品牌识别规则](#品牌识别规则)
- [自动化部署](#自动化部署)
- [数据结构](#数据结构)
- [常见修改场景](#常见修改场景)

---

## 系统概述

**功能**: 自动监控JB Hi-Fi上eufy及竞品的安防产品和母婴产品价格变化

**核心特性**:
- 每日自动抓取价格数据
- 历史价格追踪和对比
- 促销检测和日历生成
- 多品牌、多类别产品支持
- GitHub Pages自动部署展示

**产品类别** (4大类):
1. 🍼 **Baby** - 婴儿监视器、吸奶器等母婴产品
2. 📷 **Security Camera** - 安防摄像头
3. 🔔 **Video Doorbell** - 智能门铃
4. 🔐 **Smart Lock** - 智能门锁

**支持品牌**:
- **Baby**: eufy, Momcozy, Nanit, Owlet, Philips, VTech, Oricom, Medela, Uniden等
- **Security**: eufy, Arlo, Ring, Google Nest, TP-Link, Swann等
- **Doorbell**: eufy, Ring, TP-Link, Arlo, Swann等
- **Lock**: eufy, Yale, Aqara, Kaadas, Auslock等

**数据统计** (2026-03-25):
- 总产品数: 161款
- Baby产品: 49款
- Security Camera: 55款
- Video Doorbell: 26款
- Smart Lock: 31款

---

## 文件结构

```
feishu_bot/
├── .github/workflows/
│   └── update-prices-robust.yml          # GitHub Actions自动化工作流
├── price_monitor/
│   ├── daily_price_refresh.py            # 🔑 主爬虫脚本
│   ├── product_classifier.py             # 🔑 产品分类器
│   ├── price_history_manager.py          # 历史数据管理
│   ├── promotion_detector.py             # 促销检测
│   ├── promotion_calendar_generator.py   # 促销日历生成
│   ├── price_dashboard_with_tracker.html # 🔑 网站模板
│   ├── docs/
│   │   ├── index.html                    # 生成的网站（用于GitHub Pages）
│   │   ├── price_results_latest.json     # 最新价格数据
│   │   ├── price_history.json            # 历史价格数据
│   │   └── promotions.json               # 促销信息
│   ├── price_results_latest.json         # 本地最新价格
│   ├── price_history.json                # 本地历史数据
│   └── promotions.json                   # 本地促销信息
└── docs/                                  # 🔑 GitHub Pages根目录
    ├── index.html                         # 网站入口（从price_monitor/docs复制）
    ├── price_results_latest.json
    ├── price_history.json
    └── promotions.json
```

### 🔑 关键文件说明

#### 1. `daily_price_refresh.py` - 主爬虫脚本
**作用**: 搜索和抓取产品价格的核心脚本

**主要函数**:
```python
def search_all_eufy_cameras()        # 搜索eufy camera产品
def search_competitor_cameras()      # 搜索竞品camera (Arlo/Ring/Google Nest/TP-Link/Swann)
def search_doorbell_lock()           # 搜索门铃和门锁
def search_baby_products()           # 🆕 搜索所有品牌baby产品
def scrape_prices(products)          # 抓取产品价格
def main()                           # 主流程
```

**搜索关键词**:
- Baby产品: `baby monitor`, `breast pump`, `momcozy baby`, `nanit baby monitor`, `owlet baby`, `eufy baby`
- Camera: `eufy camera`, `arlo security camera`, `ring security camera`等
- Doorbell/Lock: `smart doorbell`, `video doorbell`, `smart lock`

#### 2. `product_classifier.py` - 产品分类器
**作用**: 根据产品名称自动判断品类

**分类优先级**:
```python
1. Baby (最高优先级)
   - 关键词: baby, breast pump, nursing, infant, momcozy, nanit, owlet
   - 排除: lock, deadbolt, doorbell

2. Video Doorbell
   - 关键词: doorbell, door bell, video door

3. Smart Lock
   - 关键词: lock, deadbolt, door lock, smart lock
   - 排除: unlock, lock kit

4. Security Camera (默认)
```

**主要函数**:
```python
def classify_product(product_name, brand='')  # 分类产品
def is_valid_product(product_name)            # 判断是否有效产品（排除配件）
def validate_product_data(product)            # 验证产品数据完整性
```

#### 3. `price_dashboard_with_tracker.html` - 网站模板
**作用**: 网站的HTML模板，包含所有UI和JavaScript逻辑

**关键部分**:
- **硬编码类别筛选按钮** (第682-690行):
  ```html
  <button class="filter-btn" data-category="Security Camera">📷 Security Camera</button>
  <button class="filter-btn" data-category="Video Doorbell">🔔 Video Doorbell</button>
  <button class="filter-btn" data-category="Smart Lock">🔐 Smart Lock</button>
  <button class="filter-btn" data-category="Baby">🍼 Baby</button>
  ```

- **JavaScript类别对象** (第2122-2127行):
  ```javascript
  const categories = {
      'Security Camera': { icon: '📷', products: [] },
      'Video Doorbell': { icon: '🔔', products: [] },
      'Smart Lock': { icon: '🔐', products: [] },
      'Baby': { icon: '🍼', products: [] }
  };
  ```

- **数据嵌入位置** (第719-726行):
  ```javascript
  async function loadData() {
      try {
          const data = [/* 产品数据数组 */];
  ```

#### 4. `.github/workflows/update-prices-robust.yml` - 自动化工作流
**作用**: 每天自动运行价格更新并部署

**触发条件**:
- Cron: `0 18 * * *` (每天UTC 18:00 = 北京时间凌晨2:00)
- 手动触发: workflow_dispatch

**关键步骤**:
1. 运行 `daily_price_refresh.py`
2. 使用正则替换将数据嵌入到 `price_dashboard_with_tracker.html`
3. 复制生成的HTML和JSON到根 `docs/` 目录
4. Commit并push到GitHub
5. GitHub Pages自动部署

---

## 核心功能流程

### 1. 每日价格更新流程

```
daily_price_refresh.py 执行流程:

1. 搜索产品
   ├─ search_all_eufy_cameras()      → eufy产品 (~36款)
   ├─ search_competitor_cameras()    → 竞品camera (~23款)
   ├─ search_doorbell_lock()         → 门铃门锁 (~55款)
   └─ search_baby_products()         → baby产品 (~47款)

2. 数据验证
   └─ validate_product_data()         → 验证字段完整性

3. 价格抓取
   └─ scrape_prices()                 → 并行抓取所有产品价格

4. 历史数据管理
   ├─ PriceHistoryManager.add_price_record()
   └─ PromotionDetector.detect_promotions()

5. 保存数据
   ├─ price_results_latest.json       → 最新价格
   ├─ price_history.json              → 历史价格
   └─ promotions.json                 → 促销信息

6. 生成促销日历
   └─ PromotionCalendarGenerator.generate_monthly_calendar()
```

### 2. 网站生成和部署流程

```
GitHub Actions工作流:

1. 读取数据
   ├─ price_results_latest.json
   ├─ price_history.json
   └─ promotions.json

2. 生成HTML
   ├─ 读取模板: price_dashboard_with_tracker.html
   ├─ 使用正则替换数据数组:
   │  pattern = r'(const data = )\[[\s\S]*?\];'
   │  replacement = r'\1' + json_data + ';'
   └─ 保存到: price_monitor/docs/index.html

3. 复制文件
   ├─ cp price_monitor/docs/*.json docs/
   └─ cp price_monitor/docs/index.html docs/

4. 部署
   ├─ git add docs/
   ├─ git commit -m "🤖 Auto update prices YYYY-MM-DD"
   └─ git push origin main

5. GitHub Pages自动部署
   └─ https://moeli0101.github.io/eufy-price-monitor/
```

### 3. 产品搜索流程

```
以Baby产品为例 (search_baby_products):

1. 搜索关键词循环
   ├─ "baby monitor"
   ├─ "breast pump"
   ├─ "momcozy baby"
   ├─ "nanit baby monitor"
   ├─ "owlet baby"
   └─ "eufy baby"

2. 每个关键词:
   ├─ 访问搜索页: jbhifi.com.au/search?query={term}
   ├─ 提取产品URL: 正则匹配 href="(/products/[^"]+)"
   └─ 去重: 只保留唯一URL

3. 访问每个产品详情页:
   ├─ 读取标题: page.locator('h1').first.inner_text()
   ├─ 判断是否baby产品: 关键词匹配
   ├─ 识别品牌: eufy/Momcozy/Nanit/Owlet/Philips/VTech等
   ├─ 分类产品: classify_product(title)
   └─ 添加到结果列表

4. 返回产品列表
```

---

## 产品分类系统

### 分类逻辑 (product_classifier.py)

```python
def classify_product(product_name, brand=''):
    """
    优先级顺序:
    1. Baby (最高优先级)
    2. Video Doorbell
    3. Smart Lock
    4. Security Camera (默认)
    """

    name_lower = product_name.lower()

    # 1. Baby产品判断
    baby_keywords = ['baby', 'breast pump', 'nursing', 'infant',
                     'newborn', 'sock', 'monitor baby', 'momcozy',
                     'nanit', 'owlet']
    exclude_keywords = ['lock', 'deadbolt', 'doorbell']

    has_baby_keyword = any(kw in name_lower for kw in baby_keywords)
    has_exclude = any(ex in name_lower for ex in exclude_keywords)

    if has_baby_keyword and not has_exclude:
        return 'Baby'

    # 2. Video Doorbell判断
    doorbell_keywords = ['doorbell', 'door bell', 'video door']
    if any(kw in name_lower for kw in doorbell_keywords):
        return 'Video Doorbell'

    # 3. Smart Lock判断
    lock_keywords = ['lock', 'deadbolt', 'door lock', 'smart lock']
    lock_exclusions = ['unlock', 'lock kit']

    is_lock = any(kw in name_lower for kw in lock_keywords)
    has_exclusion = any(ex in name_lower for ex in lock_exclusions)

    if is_lock and not has_exclusion:
        return 'Smart Lock'

    # 4. 默认为Security Camera
    return 'Security Camera'
```

### 有效产品判断

```python
def is_valid_product(product_name):
    """排除配件，只保留主产品"""

    # 配件关键词
    accessory_keywords = [
        'cable', 'mount', 'bracket', 'solar panel', 'adapter',
        'charging', 'charger', 'battery', 'cover', 'skin',
        'silicone cover', 'wall mount', 'ceiling mount',
        'stand alone', 'replacement'
    ]

    # 套装关键词（即使有配件词也算有效）
    valid_keywords = [
        'doorbell with chime',
        'camera with',
        'kit'
    ]

    name_lower = product_name.lower()
    is_kit = any(kw in name_lower for kw in valid_keywords)
    is_accessory = any(kw in name_lower for kw in accessory_keywords)

    return is_kit or not is_accessory
```

---

## 品牌识别规则

### Baby产品品牌识别 (search_baby_products函数)

```python
# 品牌识别逻辑
brand = 'Other'  # 默认

if 'eufy' in title_lower:
    brand = 'eufy'
elif 'momcozy' in title_lower:
    brand = 'Momcozy'
elif 'nanit' in title_lower:
    brand = 'Nanit'
elif 'owlet' in title_lower:
    brand = 'Owlet'
elif 'philips' in title_lower:
    brand = 'Philips'
elif 'vtech' in title_lower:
    brand = 'VTech'
```

**注意**: 品牌识别是按顺序匹配的，如果产品名中同时包含多个品牌词，只会匹配第一个。

### 竞品Camera品牌 (search_competitor_cameras函数)

```python
brands = [
    ('Arlo', 'arlo security camera'),
    ('Ring', 'ring security camera'),
    ('Google Nest', 'google nest cam'),
    ('TP-Link', 'tp-link tapo camera'),
    ('Swann', 'swann security camera'),
]
```

---

## 自动化部署

### GitHub Actions配置

**文件**: `.github/workflows/update-prices-robust.yml`

**触发条件**:
```yaml
on:
  schedule:
    - cron: '0 18 * * *'  # 每天UTC 18:00 (北京时间02:00)
  workflow_dispatch:      # 手动触发
```

**关键步骤**:

1. **运行爬虫**
```yaml
- name: Run price scraper
  run: |
    cd price_monitor
    python daily_price_refresh.py
```

2. **生成HTML**
```yaml
- name: Generate standalone HTML
  run: |
    cd price_monitor
    python << 'EOF'
    import json, re

    # 读取模板和数据
    with open('price_dashboard_with_tracker.html', 'r') as f:
        html = f.read()
    with open('price_results_latest.json', 'r') as f:
        data = json.load(f)

    # 替换数据
    pattern = r'(const data = )\[[\s\S]*?\];'
    replacement = r'\1' + json.dumps(data) + ';'
    html = re.sub(pattern, replacement, html)

    # 保存
    with open('docs/index.html', 'w') as f:
        f.write(html)
    EOF
```

3. **复制到根docs/**
```yaml
- name: Copy to root docs
  run: |
    mkdir -p docs
    cp price_monitor/docs/index.html docs/
    cp price_monitor/docs/*.json docs/
```

4. **提交和推送**
```yaml
- name: Commit and push
  run: |
    git config user.name "GitHub Action"
    git config user.email "action@github.com"
    git add docs/ price_monitor/
    git commit -m "🤖 Auto update prices $(date +%Y-%m-%d)"
    git push
```

### 手动触发更新

```bash
# 方法1: 本地运行
cd /Users/anker/Desktop/feishu_bot/price_monitor
python3 daily_price_refresh.py

# 方法2: GitHub网站触发
# 访问: https://github.com/moeli0101/eufy-price-monitor/actions
# 点击 "Update Prices Daily (Robust)"
# 点击 "Run workflow"
```

---

## 数据结构

### 1. price_results_latest.json

```json
[
  {
    "name": "eufy Baby Wi-Fi 2K Baby Monitor",
    "brand": "eufy",
    "category": "Baby",
    "channel": "JB Hi-Fi",
    "url": "https://www.jbhifi.com.au/products/...",
    "currency": "AUD",
    "scraped_at": "2026-03-25T10:30:00",
    "price": 159.0,
    "was_price": 229.0,           // 可选：原价
    "discount_percent": 31,       // 可选：折扣百分比
    "status": "success"
  }
]
```

### 2. price_history.json

```json
{
  "eufy_baby_wi_fi_2k_baby_monitor": {
    "product_name": "eufy Baby Wi-Fi 2K Baby Monitor",
    "brand": "eufy",
    "category": "Baby",
    "url": "https://www.jbhifi.com.au/products/...",
    "price_history": [
      {
        "date": "2026-03-23",
        "price": 159.0,
        "was_price": 229.0,
        "is_on_sale": true,
        "discount_percent": 31
      },
      {
        "date": "2026-03-24",
        "price": 159.0,
        "is_on_sale": false
      }
    ]
  }
}
```

### 3. promotions.json

```json
{
  "active_promotions": [
    {
      "product_id": "eufy_baby_wi_fi_2k_baby_monitor",
      "product_name": "eufy Baby Wi-Fi 2K Baby Monitor",
      "brand": "eufy",
      "category": "Baby",
      "url": "https://www.jbhifi.com.au/products/...",
      "start_date": "2026-03-20",
      "current_price": 159.0,
      "original_price": 229.0,
      "discount_percent": 31,
      "savings": 70.0,
      "days_running": 5
    }
  ],
  "promotion_history": [...]
}
```

---

## 常见修改场景

### 场景1: 添加新的产品类别

**示例**: 添加"Thermostats"（温控器）类别

1. **修改 `product_classifier.py`**
```python
# 在classify_product函数中添加新类别判断
def classify_product(product_name, brand=''):
    name_lower = product_name.lower()

    # 添加温控器判断（在Baby之后）
    thermostat_keywords = ['thermostat', 'temperature control', 'smart heating']
    if any(kw in name_lower for kw in thermostat_keywords):
        return 'Thermostat'

    # ... 其他判断 ...

# 更新validate_product_data中的有效类别列表
valid_categories = ['Security Camera', 'Video Doorbell', 'Smart Lock', 'Baby', 'Thermostat']
```

2. **修改 `price_dashboard_with_tracker.html`**
```html
<!-- 添加硬编码筛选按钮 (第682-690行附近) -->
<button class="filter-btn" data-category="Thermostat">🌡️ Thermostat</button>
```

```javascript
// 添加JavaScript类别对象 (第2122-2127行附近)
const categories = {
    'Security Camera': { icon: '📷', products: [] },
    'Video Doorbell': { icon: '🔔', products: [] },
    'Smart Lock': { icon: '🔐', products: [] },
    'Baby': { icon: '🍼', products: [] },
    'Thermostat': { icon: '🌡️', products: [] }  // 新增
};
```

3. **修改 `daily_price_refresh.py` 添加搜索函数**
```python
def search_thermostats():
    """搜索温控器产品"""
    print('\n🌡️ 搜索温控器产品...')
    products = []
    # ... 实现搜索逻辑 ...
    return products

# 在main()函数中调用
def main():
    # ...
    thermostat_products = search_thermostats()
    all_products = eufy_products + competitor_products + doorbell_lock_products + baby_products + thermostat_products
```

4. **重新生成HTML并部署**
```bash
cd /Users/anker/Desktop/feishu_bot/price_monitor
python3 daily_price_refresh.py
# 然后提交到GitHub
```

### 场景2: 添加新的Baby产品品牌

**示例**: 添加"Elvie"吸奶器品牌

1. **修改 `product_classifier.py`**
```python
# 在baby_keywords中添加品牌关键词
baby_keywords = ['baby', 'breast pump', 'nursing', 'infant',
                 'newborn', 'sock', 'monitor baby', 'momcozy',
                 'nanit', 'owlet', 'elvie']  # 添加elvie
```

2. **修改 `daily_price_refresh.py`**
```python
# 在search_baby_products函数中添加搜索关键词
search_terms = [
    'baby monitor',
    'breast pump',
    'momcozy baby',
    'nanit baby monitor',
    'owlet baby',
    'eufy baby',
    'elvie breast pump'  # 新增
]

# 在品牌识别中添加Elvie
brand = 'Other'
if 'eufy' in title_lower:
    brand = 'eufy'
elif 'momcozy' in title_lower:
    brand = 'Momcozy'
# ... 其他品牌 ...
elif 'elvie' in title_lower:
    brand = 'Elvie'  # 新增
```

3. **运行更新并部署**
```bash
cd /Users/anker/Desktop/feishu_bot/price_monitor
python3 daily_price_refresh.py
```

### 场景3: 修改自动更新时间

**修改 `.github/workflows/update-prices-robust.yml`**

```yaml
# 当前: 每天UTC 18:00 (北京时间02:00)
on:
  schedule:
    - cron: '0 18 * * *'

# 改为: 每天UTC 12:00 (北京时间20:00)
on:
  schedule:
    - cron: '0 12 * * *'

# 改为: 每天UTC 6:00和18:00 (北京时间14:00和02:00)
on:
  schedule:
    - cron: '0 6,18 * * *'
```

**Cron语法**:
```
* * * * *
│ │ │ │ │
│ │ │ │ └─ 星期 (0-6, 0=Sunday)
│ │ │ └─── 月份 (1-12)
│ │ └───── 日期 (1-31)
│ └─────── 小时 (0-23)
└───────── 分钟 (0-59)
```

### 场景4: 添加价格区间筛选

**修改 `price_dashboard_with_tracker.html`**

在第692-700行附近的价格筛选部分，添加新的价格区间：

```html
<div class="filter-section">
    <span class="filter-label">价格区间</span>
    <div class="filter-buttons" id="priceFilters">
        <button class="filter-btn active" data-price="all">全部价格</button>
        <button class="filter-btn" data-price="0-100">$0-$100</button>    <!-- 新增 -->
        <button class="filter-btn" data-price="100-200">$100-$200</button> <!-- 新增 -->
        <button class="filter-btn" data-price="0-200">$0-$200</button>
        <button class="filter-btn" data-price="200-400">$200-$400</button>
        <button class="filter-btn" data-price="400-700">$400-$700</button>
        <button class="filter-btn" data-price="700-1200">$700-$1200</button>
        <button class="filter-btn" data-price="1200-99999">$1200+</button>
    </div>
</div>
```

### 场景5: 更新网站而不运行爬虫

**快速更新流程**:

```bash
cd /Users/anker/Desktop/feishu_bot/price_monitor

# 1. 修改模板HTML
# vim price_dashboard_with_tracker.html

# 2. 重新生成网站HTML（使用现有数据）
python3 << 'EOF'
import json, re, shutil

with open('price_dashboard_with_tracker.html', 'r') as f:
    html = f.read()
with open('price_results_latest.json', 'r') as f:
    data = json.load(f)

json_data = json.dumps(data, ensure_ascii=False, indent=2)
pattern = r'(const data = )\[[\s\S]*?\];'
replacement = r'\1' + json_data + ';'
html = re.sub(pattern, replacement, html, count=1)

with open('docs/index.html', 'w') as f:
    f.write(html)
shutil.copy('docs/index.html', '/Users/anker/Desktop/feishu_bot/docs/index.html')
print('✅ HTML已更新')
EOF

# 3. 提交到GitHub
cd /Users/anker/Desktop/feishu_bot
git add docs/index.html price_monitor/price_dashboard_with_tracker.html
git commit -m "🎨 更新网站UI"
git push origin main
```

---

## 故障排查

### 问题1: 网站显示旧数据

**原因**: 浏览器缓存

**解决方法**:
1. 强制刷新: **Cmd + Shift + R** (Mac) 或 **Ctrl + Shift + R** (Windows)
2. 清除缓存: **Cmd + Option + E** (Mac)
3. 使用无痕窗口: **Cmd + Shift + N** (Mac)

### 问题2: GitHub Actions失败

**检查步骤**:
1. 访问: https://github.com/moeli0101/eufy-price-monitor/actions
2. 点击失败的workflow run
3. 查看错误日志
4. 常见错误:
   - 超时: 增加timeout配置
   - 依赖问题: 检查Python依赖安装
   - Git冲突: 手动解决冲突后重新运行

### 问题3: Baby产品筛选按钮不显示

**检查清单**:
1. ✅ HTML中是否有硬编码的Baby按钮？
   - 文件: `price_dashboard_with_tracker.html` 第682-690行
2. ✅ JavaScript categories对象中是否有Baby？
   - 文件: `price_dashboard_with_tracker.html` 第2122-2127行
3. ✅ 数据中是否有Baby类别的产品？
   - 检查: `price_results_latest.json`
4. ✅ HTML是否已重新生成并部署？
   - 运行生成脚本并推送到GitHub

### 问题4: 产品分类错误

**调试方法**:
```bash
cd /Users/anker/Desktop/feishu_bot/price_monitor

# 测试分类器
python3 << 'EOF'
from product_classifier import classify_product

test_products = [
    "Momcozy S12 Pro Wearable Breast Pump",
    "eufy Baby Wi-Fi 2K Baby Monitor",
    "eufy Security C210 2K Camera",
    "Ring Video Doorbell",
    "Yale Smart Lock"
]

for name in test_products:
    category = classify_product(name)
    print(f"{name}\n  → {category}\n")
EOF
```

---

## 性能优化建议

### 1. 并行抓取价格
当前: 顺序抓取（每个产品1-2秒）
优化: 使用多线程/多进程并行抓取

### 2. 增量更新
当前: 每次全量抓取所有产品
优化: 只抓取价格变化的产品

### 3. 缓存搜索结果
当前: 每次重新搜索产品URL
优化: 缓存产品URL列表，定期更新

### 4. 减少页面等待时间
当前: 固定等待5秒
优化: 使用wait_for_selector等待特定元素加载

---

## 联系和维护

**项目地址**: https://github.com/moeli0101/eufy-price-monitor
**网站地址**: https://moeli0101.github.io/eufy-price-monitor/
**开发者**: moe.li@anker.com

**维护清单**:
- [ ] 每周检查GitHub Actions运行状态
- [ ] 每月检查数据准确性
- [ ] 季度检查JB Hi-Fi网站结构是否改变
- [ ] 根据需求添加新产品类别和品牌

---

## 版本历史

### v2.0 (2026-03-25)
- ✅ 添加多品牌母婴产品支持
- ✅ 新增Momcozy、Nanit、Owlet、Philips、VTech等品牌
- ✅ Baby产品从12款增加到49款
- ✅ 总产品数从117款增加到161款
- ✅ 改进产品分类器支持更多baby关键词

### v1.1 (2026-03-24)
- ✅ 添加Baby产品类别
- ✅ 修复筛选器显示问题
- ✅ 优化价格追踪功能
- ✅ 添加自动初始化代码

### v1.0 (2026-03-23)
- ✅ 初始版本
- ✅ 支持eufy产品价格监控
- ✅ 支持竞品对比
- ✅ 自动化部署到GitHub Pages

---

**文档结束**
