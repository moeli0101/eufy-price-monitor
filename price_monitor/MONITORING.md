# 价格监控系统 - 运维手册

## 📊 系统健康监控

### 快速检查
```bash
cd /Users/anker/Desktop/feishu_bot/price_monitor
python3 health_check.py
```

### GitHub Actions 状态
访问：https://github.com/moeli0101/eufy-price-monitor/actions

---

## ⚠️ 已知风险与解决方案

### 1. 🔴 **Playwright依赖安装失败**

**症状：**
```
Error: Failed to install browsers
```

**原因：**
- Chromium下载超时
- 网络不稳定

**解决方案：**
✅ 使用缓存加速（已在workflow中配置）
```yaml
- name: Cache Playwright browsers
  uses: actions/cache@v3
```

✅ 手动触发重试：
- 进入 Actions 标签页
- 点击 "Update Prices Daily (Robust)"
- 点击 "Run workflow"

---

### 2. 🔴 **抓取失败（网络/反爬虫）**

**症状：**
```
ERROR: price_history.json not generated
```

**原因：**
- JB Hi-Fi封禁IP
- 网页结构改变
- 网络超时

**解决方案：**

✅ **立即恢复**（使用昨天数据）：
```bash
cd price_monitor
git checkout HEAD~1 -- price_history.json
git add price_history.json
git commit -m "🔧 使用昨天的数据"
git push
```

✅ **修复反爬虫**：
- 增加随机延迟
- 轮换User-Agent
- 使用代理IP（如果需要）

✅ **修复选择器**：
检查JB Hi-Fi页面是否改版，更新选择器

---

### 3. 🟡 **数据过期（>2天）**

**症状：**
```
数据过期 3 天（最新: 2026-03-18）
```

**原因：**
- GitHub Actions未运行
- Cron job配置错误

**解决方案：**

✅ **检查cron配置**：
```yaml
schedule:
  - cron: '0 18 * * *'  # 确认时间正确
```

✅ **手动运行**：
```bash
cd price_monitor
python3 daily_price_refresh.py
```

✅ **检查GitHub Actions配额**：
- 免费账户：2000分钟/月
- 查看：Settings → Billing → Actions

---

### 4. 🟡 **Git推送冲突**

**症状：**
```
! [rejected] main -> main (non-fast-forward)
```

**原因：**
- 本地和远程同时修改
- Actions推送冲突

**解决方案：**

✅ **自动重试**（已配置）：
```bash
for i in 1 2 3; do
  git pull --rebase && git push && break
done
```

✅ **手动解决**：
```bash
cd /Users/anker/Desktop/feishu_bot
git fetch origin
git rebase origin/main
git push
```

---

### 5. 🟢 **产品名称变化导致ID重复**

**症状：**
同一产品生成两个不同ID，历史数据断裂

**预防：**
- 使用稳定的产品标识符（SKU、URL）
- 定期清理重复数据

**解决方案：**
```python
# 未来优化：使用URL作为主键
product_id = hashlib.md5(product_url.encode()).hexdigest()[:16]
```

---

## 📈 每日运行检查清单

### 自动检查（GitHub Actions）
- ✅ 每天UTC 18:00运行
- ✅ 失败时创建Issue
- ✅ 日志保存7天

### 手动检查（建议每周一次）

**1. 检查数据新鲜度**
```bash
cd price_monitor
python3 health_check.py
```

**2. 查看GitHub Actions历史**
- 访问：https://github.com/moeli0101/eufy-price-monitor/actions
- 确认最近7天都成功运行

**3. 验证网站可访问**
- 访问：https://moeli0101.github.io/eufy-price-monitor/price_tracker.html
- 检查数据是否更新
- 测试产品选择和图表

**4. 检查产品数量**
```bash
cat price_history.json | python3 -c "import json, sys; print(len(json.load(sys.stdin)))"
```
应该 ≥ 70 个产品

---

## 🚨 紧急恢复流程

### 情况1：数据损坏

```bash
# 1. 从Git历史恢复
cd /Users/anker/Desktop/feishu_bot
git log --oneline price_monitor/price_history.json  # 查看历史
git checkout <commit-hash> -- price_monitor/price_history.json

# 2. 推送修复
git add price_monitor/price_history.json
git commit -m "🔧 恢复数据"
git push
```

### 情况2：完全失败超过3天

```bash
# 重新抓取
cd price_monitor
python3 daily_price_refresh.py

# 验证
python3 health_check.py

# 推送
cd ..
git add price_monitor/
git commit -m "🔧 重新抓取数据"
git push
```

### 情况3：GitHub Actions完全失效

**Plan B：本地定时任务**

```bash
# 创建cron任务
crontab -e

# 添加（每天凌晨2点运行）
0 2 * * * cd /Users/anker/Desktop/feishu_bot/price_monitor && python3 daily_price_refresh.py && git add . && git commit -m "🤖 Local update" && git push
```

---

## 📊 监控指标

### 关键指标

| 指标 | 正常值 | 警告值 | 操作 |
|------|--------|--------|------|
| 产品数量 | ≥70 | <60 | 检查抓取逻辑 |
| 数据新鲜度 | ≤1天 | >2天 | 手动运行 |
| 历史天数 | 累积增长 | 不增长 | 检查追加逻辑 |
| 促销产品 | 10-30 | <5 或 >50 | 验证促销检测 |
| Actions成功率 | 100% | <95% | 检查日志 |

### 查看实时指标

**产品数量：**
```bash
cat price_history.json | python3 -c "import json, sys; print('产品:', len(json.load(sys.stdin)))"
```

**历史天数：**
```bash
cat price_history.json | python3 -c "import json, sys; d=json.load(sys.stdin); print('最长历史:', max(len(p['price_history']) for p in d.values()), '天')"
```

**促销数量：**
```bash
cat promotions.json | python3 -c "import json, sys; print('促销:', len(json.load(sys.stdin)))"
```

---

## 🔔 告警配置

### GitHub Issues自动创建
✅ 已配置：失败时自动创建Issue

### 邮件通知（可选）
在 GitHub → Settings → Notifications → Actions 中配置

### 企业微信通知（可选）
可以添加webhook发送到企业微信群

---

## 📝 日志查看

### GitHub Actions日志
1. 进入 https://github.com/moeli0101/eufy-price-monitor/actions
2. 点击最近的运行
3. 展开步骤查看详细日志

### 本地日志
```bash
# 抓取日志
cat price_monitor/scrape.log

# 刷新日志
cat price_monitor/price_refresh_log.json | python3 -m json.tool
```

---

## 🎯 性能优化建议

### 当前运行时间
预计 15-30 分钟

### 优化方向
1. **并行抓取**：使用异步或多线程
2. **增量更新**：只抓取有变化的产品
3. **缓存结果**：相同产品一天只抓取一次
4. **使用API**：如果JB Hi-Fi提供API

---

## ✅ 成功标准

### 每日目标
- ✅ 抓取成功率 100%
- ✅ 数据延迟 <24小时
- ✅ 产品覆盖率 >95%

### 长期目标
- ✅ 积累 90天+ 历史数据
- ✅ 零数据丢失
- ✅ 自动化运维，无需人工干预

---

## 📞 联系方式

如有问题：
1. 查看 GitHub Issues
2. 查看 Actions 运行日志
3. 运行 health_check.py 诊断
