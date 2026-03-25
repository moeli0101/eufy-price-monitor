# 快速参考指南

> 最后更新: 2026-03-25

## 🚀 常用命令

### 运行价格更新
```bash
cd /Users/anker/Desktop/feishu_bot/price_monitor
python3 daily_price_refresh.py
```

### 重新生成网站（使用现有数据）
```bash
cd /Users/anker/Desktop/feishu_bot/price_monitor
python3 << 'EOF'
import json, re, shutil

with open('price_dashboard_with_tracker.html', 'r') as f:
    html = f.read()
with open('price_results_latest.json', 'r') as f:
    data = json.load(f)

json_data = json.dumps(data, ensure_ascii=False, indent=2)
pattern = r'(async function loadData\(\) \{\s*try \{\s*// 数据直接内嵌在页面中\s*const data = )\[[\s\S]*?\];'
replacement = r'\1' + json_data + ';'
html = re.sub(pattern, replacement, html, count=1)

with open('docs/index.html', 'w') as f:
    f.write(html)
shutil.copy('docs/index.html', '/Users/anker/Desktop/feishu_bot/docs/index.html')
print('✅ HTML已更新')
EOF
```

### 查看数据统计
```bash
cd /Users/anker/Desktop/feishu_bot/price_monitor
python3 << 'EOF'
import json
from collections import Counter

with open('price_results_latest.json', 'r') as f:
    data = json.load(f)

print(f"总产品数: {len(data)}")
print("\n类别分布:")
categories = Counter([p['category'] for p in data])
for cat, count in sorted(categories.items()):
    print(f"  {cat}: {count}款")

print("\nBaby产品品牌:")
baby = [p for p in data if p['category'] == 'Baby']
brands = Counter([p['brand'] for p in baby])
for brand, count in sorted(brands.items(), key=lambda x: -x[1]):
    print(f"  {brand}: {count}款")
EOF
```

### 提交到GitHub
```bash
cd /Users/anker/Desktop/feishu_bot
git add price_monitor/ docs/
git commit -m "🔄 更新价格数据"
git push origin main
```

### 检查GitHub Actions状态
```bash
curl -s "https://api.github.com/repos/moeli0101/eufy-price-monitor/actions/runs?per_page=5" | python3 -c "import sys, json; runs = json.load(sys.stdin)['workflow_runs']; [print(f\"{r['created_at'][:10]} {r['created_at'][11:19]} - {r['name']} - {r['conclusion'] or r['status']}\") for r in runs[:5]]"
```

---

## 📁 关键文件位置

```
核心代码文件:
├── price_monitor/daily_price_refresh.py          # 主爬虫脚本
├── price_monitor/product_classifier.py           # 产品分类器
├── price_monitor/price_dashboard_with_tracker.html  # 网站模板
└── .github/workflows/update-prices-robust.yml    # 自动化工作流

数据文件:
├── price_monitor/price_results_latest.json       # 最新价格（本地）
├── price_monitor/price_history.json              # 历史数据（本地）
├── price_monitor/promotions.json                 # 促销信息（本地）
├── docs/price_results_latest.json                # 最新价格（网站）
├── docs/price_history.json                       # 历史数据（网站）
└── docs/promotions.json                          # 促销信息（网站）

网站文件:
├── price_monitor/docs/index.html                 # 生成的网站
└── docs/index.html                               # 部署到GitHub Pages的网站
```

---

## 🔧 快速修改指南

### 添加新品牌到Baby产品

**位置**: `daily_price_refresh.py` 的 `search_baby_products()` 函数

```python
# 1. 添加搜索关键词
search_terms = [
    'baby monitor',
    'breast pump',
    'momcozy baby',
    '新品牌名 baby',  # 添加这里
]

# 2. 添加品牌识别
if 'eufy' in title_lower:
    brand = 'eufy'
elif 'momcozy' in title_lower:
    brand = 'Momcozy'
elif '新品牌名' in title_lower:
    brand = '新品牌名'  # 添加这里
```

**位置**: `product_classifier.py` 的 `classify_product()` 函数

```python
# 添加品牌关键词
baby_keywords = ['baby', 'breast pump', 'nursing', 'infant',
                 'newborn', 'sock', 'monitor baby', 'momcozy',
                 'nanit', 'owlet', '新品牌名']  # 添加这里
```

### 添加新产品类别

**步骤1**: 修改 `product_classifier.py`
```python
# 在classify_product函数中添加判断逻辑
def classify_product(product_name, brand=''):
    name_lower = product_name.lower()

    # 添加新类别判断（注意优先级）
    if '新类别关键词' in name_lower:
        return '新类别名称'

    # ... 其他判断 ...

# 更新有效类别列表
valid_categories = ['Security Camera', 'Video Doorbell',
                    'Smart Lock', 'Baby', '新类别名称']
```

**步骤2**: 修改 `price_dashboard_with_tracker.html`
```html
<!-- 添加筛选按钮 (第682-690行附近) -->
<button class="filter-btn" data-category="新类别名称">🆕 新类别名称</button>
```

```javascript
// 添加类别对象 (第2122-2127行附近)
const categories = {
    'Security Camera': { icon: '📷', products: [] },
    'Video Doorbell': { icon: '🔔', products: [] },
    'Smart Lock': { icon: '🔐', products: [] },
    'Baby': { icon: '🍼', products: [] },
    '新类别名称': { icon: '🆕', products: [] }
};
```

**步骤3**: 修改 `daily_price_refresh.py`
```python
# 添加搜索函数
def search_新类别():
    """搜索新类别产品"""
    print('\n🆕 搜索新类别产品...')
    products = []
    # ... 实现逻辑 ...
    return products

# 在main()中调用
def main():
    # ...
    新类别_products = search_新类别()
    all_products = eufy_products + ... + 新类别_products
```

### 修改自动更新时间

**位置**: `.github/workflows/update-prices-robust.yml`

```yaml
# 当前配置 (每天UTC 18:00)
on:
  schedule:
    - cron: '0 18 * * *'

# 常用时间示例:
# - cron: '0 6 * * *'    # 每天UTC 06:00 (北京时间14:00)
# - cron: '0 12 * * *'   # 每天UTC 12:00 (北京时间20:00)
# - cron: '0 0 * * *'    # 每天UTC 00:00 (北京时间08:00)
# - cron: '0 6,18 * * *' # 每天UTC 06:00和18:00 (两次)
```

**Cron时间转换**:
- UTC 0:00 = 北京时间 8:00
- UTC 6:00 = 北京时间 14:00
- UTC 12:00 = 北京时间 20:00
- UTC 18:00 = 北京时间 2:00 (次日)

---

## 🐛 故障排查

### 网站显示旧数据
```bash
# 解决方法1: 强制刷新浏览器
# Mac: Cmd + Shift + R
# Windows: Ctrl + Shift + R

# 解决方法2: 清除缓存
# Mac: Cmd + Option + E

# 解决方法3: 使用无痕窗口
# Mac: Cmd + Shift + N
```

### GitHub Actions失败
```bash
# 1. 查看日志
# 访问: https://github.com/moeli0101/eufy-price-monitor/actions

# 2. 手动触发workflow
# 在Actions页面点击 "Run workflow"

# 3. 本地运行测试
cd /Users/anker/Desktop/feishu_bot/price_monitor
python3 daily_price_refresh.py
```

### 产品分类错误
```bash
cd /Users/anker/Desktop/feishu_bot/price_monitor

# 测试分类器
python3 << 'EOF'
from product_classifier import classify_product

products = [
    "测试产品名称1",
    "测试产品名称2"
]

for name in products:
    category = classify_product(name)
    print(f"{name} → {category}")
EOF
```

### 筛选按钮不显示
```bash
# 检查清单:
# 1. ✅ HTML中硬编码的按钮 (price_dashboard_with_tracker.html:682-690)
# 2. ✅ JavaScript categories对象 (price_dashboard_with_tracker.html:2122-2127)
# 3. ✅ 数据中有该类别的产品 (price_results_latest.json)
# 4. ✅ HTML已重新生成并部署

# 验证数据
cd /Users/anker/Desktop/feishu_bot/price_monitor
python3 -c "import json; data = json.load(open('price_results_latest.json')); print(set([p['category'] for p in data]))"
```

---

## 📊 数据查询

### 查看产品数量
```bash
cd /Users/anker/Desktop/feishu_bot/price_monitor
python3 -c "import json; print(f\"总产品数: {len(json.load(open('price_results_latest.json')))}\")"
```

### 查看类别分布
```bash
cd /Users/anker/Desktop/feishu_bot/price_monitor
python3 -c "import json; from collections import Counter; data = json.load(open('price_results_latest.json')); print('\n'.join([f'{k}: {v}款' for k,v in Counter([p['category'] for p in data]).items()]))"
```

### 查看Baby产品列表
```bash
cd /Users/anker/Desktop/feishu_bot/price_monitor
python3 << 'EOF'
import json
data = json.load(open('price_results_latest.json'))
baby = [p for p in data if p['category'] == 'Baby']
for p in baby:
    status = '🔥' if p.get('was_price') else ''
    print(f"{p['brand']:12} ${p['price']:6.2f} {status} {p['name']}")
EOF
```

### 查看促销产品
```bash
cd /Users/anker/Desktop/feishu_bot/price_monitor
python3 << 'EOF'
import json
data = json.load(open('price_results_latest.json'))
on_sale = [p for p in data if p.get('was_price')]
print(f"促销产品: {len(on_sale)}款\n")
for p in on_sale:
    discount = p.get('discount_percent', 0)
    print(f"{p['brand']:12} -{discount:2d}% ${p['was_price']:6.2f} → ${p['price']:6.2f} {p['name'][:50]}")
EOF
```

### 查看价格历史
```bash
cd /Users/anker/Desktop/feishu_bot/price_monitor
python3 << 'EOF'
import json
history = json.load(open('price_history.json'))
product_id = 'eufy_baby_wi_fi_2k_baby_monitor'  # 修改这里

if product_id in history:
    product = history[product_id]
    print(f"产品: {product['product_name']}\n")
    print("价格历史:")
    for record in product['price_history']:
        status = '🔥' if record.get('is_on_sale') else ''
        print(f"  {record['date']}: ${record['price']} {status}")
else:
    print(f"未找到产品: {product_id}")
EOF
```

---

## 🔗 重要链接

- **网站地址**: https://moeli0101.github.io/eufy-price-monitor/
- **GitHub仓库**: https://github.com/moeli0101/eufy-price-monitor
- **GitHub Actions**: https://github.com/moeli0101/eufy-price-monitor/actions
- **JB Hi-Fi**: https://www.jbhifi.com.au/

---

## 📝 Git提交模板

```bash
# 添加新功能
git commit -m "✨ 添加XXX功能"

# 修复bug
git commit -m "🐛 修复XXX问题"

# 更新数据
git commit -m "🔄 更新价格数据 $(date +%Y-%m-%d)"

# 优化代码
git commit -m "♻️ 重构XXX模块"

# 更新文档
git commit -m "📝 更新文档"

# UI改进
git commit -m "💄 优化网站UI"

# 性能优化
git commit -m "⚡️ 优化XXX性能"
```

---

## ⏱️ 执行时间参考

| 操作 | 预计时间 |
|------|---------|
| 完整价格更新 (161款产品) | 8-12分钟 |
| 只搜索产品 (不抓价格) | 3-5分钟 |
| 重新生成HTML | 5秒 |
| GitHub Pages部署 | 1-2分钟 |
| 手动触发workflow | 10-15分钟 |

---

## 🔔 注意事项

1. **修改HTML模板后一定要重新生成**: 修改 `price_dashboard_with_tracker.html` 后必须运行生成脚本，否则更改不会体现在网站上。

2. **数据文件需要同步**: 本地 `price_monitor/` 和根 `docs/` 目录的JSON文件要保持一致。

3. **浏览器缓存**: 部署后看不到变化通常是浏览器缓存，强制刷新即可。

4. **GitHub Actions时间**: Cron使用UTC时间，北京时间 = UTC + 8小时。

5. **产品分类优先级**: Baby > Video Doorbell > Smart Lock > Security Camera (默认)

6. **品牌识别顺序**: 按if-elif顺序匹配，第一个匹配的品牌即为最终结果。

7. **数据验证**: 运行爬虫前建议先备份 `price_history.json`。

---

**快速问题？查看完整文档**: `SYSTEM_ARCHITECTURE.md`
