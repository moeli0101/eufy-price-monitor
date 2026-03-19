# 小moe完整配置清单

**最后更新：** 2026-03-19 14:37
**状态：** ✅ 运行中

---

## 🤖 基础信息

### 飞书凭证
- **App ID:** cli_a93bbc2b02369bd6
- **App Secret:** U3Njja1yPuc7Nqqz96Rl4bA74DUGpbl0
- **应用名称:** 小moe

### AIME API
- **API Key:** app-BUXRqbg1Z98MIvMqIi5BA8Bj
- **API URL:** https://ai.anker-in.com/v1/chat-messages

### 多维表格（知识库）
- **BITABLE_APP_TOKEN:** CKDJbGdKiagfBpsBl7GccxvZnWd
- **BITABLE_TABLE_ID:** tblQ5Ev8TQlmutDS

---

## 👤 人设配置

### 基础人设（已配置 ✅）
- **性别:** 女生
- **生日:** 3月12日
- **星座:** 双鱼座
- **主人:** moe li（聪明漂亮善良）

### 详细人设（待补充 ⚠️）
需要用户提供以下信息：
- **喜欢的食物:** ？
- **兴趣爱好:** ？
- **性格特点:** ？
- **说话风格:** ？
- **特殊技能:** ？

---

## 📚 知识库内容

当前知识库共 **7篇文档**：

1. **智慧屏** - bundle调研
2. **套装化** - ifa调研
3. **agent洞察** - AI Agent洞察报告
4. **基站与eufy生态转化** - eufy生态转化路径
5. **大盘** - IOT市场盘点
6. **竞品分析** - IOT GTM竞手洞察
7. **澳洲** - 经营gap分析

---

## ⏰ 定时任务

### 日报功能
- **状态:** ⭕ 已禁用
- **原配置群ID:** oc_67ac5e1156fc3e8f86742f98ccc7a30c（可能是金融群）
- **发送时间:** 08:00
- **待确认:** 需要重新配置正确的群ID

---

## 🗂️ 产品库

**状态:** ❌ 丢失
- product_database.json 文件不见了
- 需要重新导入产品数据

---

## 🔧 技术配置

### SSL修复
- ✅ 已应用websockets库的SSL验证patch
- 解决了企业网络的证书验证问题

### 文件位置
- **bot.py:** `/Users/anker/Desktop/feishu_bot/bot.py`
- **知识库:** `/Users/anker/Desktop/feishu_bot/knowledge_base_generated.py`
- **重启脚本:** `/Users/anker/Desktop/feishu_bot/restart_moe.sh`
- **备份脚本:** `/Users/anker/Desktop/feishu_bot/backup_xiaomoe.sh`

---

## 🔒 备份机制（已建立 ✅）

### Git版本控制
- 仓库位置: `/Users/anker/Desktop/feishu_bot/.git`
- 最新提交: 2026-03-19 14:37

### 自动备份
- **备份目录:** `/Users/anker/Desktop/feishu_bot_backups`
- **备份脚本:** `./backup_xiaomoe.sh`
- **保留策略:** 最近10次备份

### 执行备份
```bash
cd /Users/anker/Desktop/feishu_bot
./backup_xiaomoe.sh
```

---

## 📝 操作记录

### 2026-03-19
- ❌ bot.py文件丢失（原因未知）
- ✅ 从.pyc成功恢复知识库（7篇文档）
- ✅ 从SOP文档恢复配置（BITABLE、日报群ID）
- ✅ 修复SSL连接问题（websockets patch）
- ✅ 建立Git版本控制
- ✅ 创建自动备份脚本
- ⭕ 禁用日报功能（待重新配置）
- ⚠️ 详细人设丢失（待用户补充）

---

## ⚠️ 待办事项

- [ ] 补充小moe的详细人设（爱好、食物、性格等）
- [ ] 确认日报功能是否需要，以及发送到哪个群
- [ ] 恢复产品库（product_database.json）
- [ ] 定期执行备份脚本（建议每天一次）

---

## 🆘 紧急恢复

如果小moe再次丢失，恢复步骤：

1. **从Git恢复:**
   ```bash
   cd /Users/anker/Desktop/feishu_bot
   git checkout bot.py
   git checkout knowledge_base_generated.py
   ```

2. **从备份恢复:**
   ```bash
   cd /Users/anker/Desktop/feishu_bot_backups
   ls -lt bot_*.py | head -1  # 找最新备份
   cp bot_20260319_143733.py ../bot.py
   ```

3. **重启小moe:**
   ```bash
   cd /Users/anker/Desktop/feishu_bot
   ./restart_moe.sh
   ```

---

**保证机制:**
✅ Git版本控制
✅ 自动备份到独立目录
✅ 本配置清单记录所有关键信息
