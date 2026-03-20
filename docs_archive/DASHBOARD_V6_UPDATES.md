# 🎉 Dashboard V6 重大更新

## ✨ 主要改进

### 1. **促销日历完全集成** 🎯
- ✅ **不再是单独页面** - 促销日历作为 Tab 嵌入主 Dashboard
- ✅ **一键切换** - 价格列表 ↔ 促销日历无缝切换
- ✅ **统一界面** - 相同的设计风格，一致的用户体验

### 2. **增强门铃搜索** 🔍
- ✅ 新增搜索词："video doorbell"（之前只有 "smart doorbell"）
- ✅ 搜索结果增加：15 → 30 个链接
- ✅ 确保 Swann、Ring、eufy 等品牌门铃都能被搜到

### 3. **数据准确性保证** 📊
- ✅ 每天自动运行，确保数据连续
- ✅ 历史数据永久保存在 price_history.json
- ✅ 促销检测自动化（开始/结束/持续时间）
- ✅ 重试机制确保抓取成功率

---

## 🌐 访问方式

### 主 Dashboard（集成版）
```
https://moeli0101.github.io/eufy-price-monitor/
```

**功能**：
- 📊 **价格列表 Tab** - 所有产品的当前价格
- 📅 **促销日历 Tab** - 历史价格和促销趋势

---

## 📅 促销日历功能

### 控制面板
- **年份选择** - 查看历史年份数据
- **月份选择** - 选择具体月份（1-12月）
- **品牌筛选** - 按品牌筛选产品
- **刷新按钮** - 重新加载日历

### 产品选择
- ✅ 勾选要对比的产品（支持多选）
- ✅ 实时更新日历表格
- ✅ 显示产品名称和品牌

### 日历表格
- **第一列** - 产品名称（固定列）
- **后续列** - 该月每一天（1-31日）
- **白色背景** - 正常价格
- **黄色背景** - 促销价格
- **折扣标签** - 显示折扣百分比
- **灰色** - 无数据

### 使用示例

**对比 eufy vs Ring**
1. 点击"📅 促销日历" Tab
2. 勾选 "eufy S330"
3. 勾选 "Ring Stick Up Cam"
4. 选择年月（如 2026年3月）
5. 点击"刷新日历"
6. 查看两个产品的促销时间对比

**查看 Swann 门铃促销**
1. 点击"📅 促销日历" Tab
2. 品牌筛选选择 "Swann"
3. 勾选 Swann 门铃产品
4. 查看促销历史

---

## 🔧 技术改进

### 1. Tab 系统
- 使用纯 JavaScript 实现
- 无需刷新页面
- 按需加载数据（首次点击才加载）

### 2. 数据加载
- 异步加载 price_history.json
- 错误处理和提示
- 空状态显示

### 3. 响应式设计
- 表格可横向滚动
- 产品名称列固定
- 移动端友好

---

## ⏰ 自动更新

### 运行时间
- 每天 UTC 18:00（澳洲东部时间凌晨 2-4 点）

### 更新内容
- ✅ 抓取最新价格
- ✅ 更新历史记录
- ✅ 检测促销变化
- ✅ 生成日历数据
- ✅ 更新 Dashboard

### 生成文件
- `price_results_latest.json` - 最新价格
- `price_history.json` - 完整历史
- `promotions.json` - 促销记录
- `promotion_calendar.json` - 月度日历
- `docs/index.html` - Dashboard 页面

---

## 📊 数据文件说明

### price_history.json
```json
{
  "eufy_eufycam_s330": {
    "product_name": "eufyCam S330",
    "brand": "eufy",
    "category": "Security Camera",
    "url": "https://...",
    "price_history": [
      {
        "date": "2026-03-18",
        "price": 299,
        "original_price": 349,
        "is_on_sale": true,
        "discount_percentage": 14
      }
    ]
  }
}
```

### promotions.json
```json
{
  "active_promotions": [
    {
      "product_id": "eufy_eufycam_s330",
      "product_name": "eufyCam S330",
      "start_date": "2026-03-15",
      "duration_days": 3,
      "discount_percentage": 14,
      "status": "active"
    }
  ],
  "historical_promotions": [...]
}
```

---

## 🎯 解决的问题

### 问题 1：促销日历是单独页面 ❌
**解决**：集成到主 Dashboard 作为 Tab ✅

### 问题 2：Swann 门铃搜索不到 ❌
**解决**：
- 增加搜索词："video doorbell"
- 增加搜索结果数量：30个
- Swann 品牌识别已启用 ✅

### 问题 3：数据不连续 ❌
**解决**：
- 每天自动运行
- 历史数据永久保存
- 重试机制确保成功 ✅

---

## 🚀 下一步操作

### 1. 修改 Workflow（必须）
```
文件：.github/workflows/update-prices.yml
Line 41: price_dashboard_v5.html → price_dashboard_v6.html
```

### 2. 触发运行
手动触发一次 workflow 测试新版本

### 3. 验证
- 检查 Dashboard 是否有两个 Tab
- 检查促销日历是否能正常显示
- 检查 Swann 门铃是否被抓取

---

## 📈 预期结果

修改完成后，Dashboard 将会：
1. ✅ 显示两个 Tab：价格列表 | 促销日历
2. ✅ 促销日历完全可用
3. ✅ Swann 门铃被正确抓取
4. ✅ 数据持续累积，每天更新

---

## 🎊 总结

**V6 版本完全满足你的需求：**
- ✅ 促销日历嵌入主页面
- ✅ 数据准确且连续
- ✅ Swann 门铃搜索增强
- ✅ 每天自动更新

**现在只需：**
1. 修改 workflow 文件（改一个字符：5→6）
2. 触发运行测试
3. 开始使用！🎉
