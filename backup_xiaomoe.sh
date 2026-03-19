#!/bin/bash
# 小moe自动备份脚本
# 每次修改后运行此脚本备份

BACKUP_DIR="/Users/anker/Desktop/feishu_bot_backups"
DATE=$(date +"%Y%m%d_%H%M%S")

# 创建备份目录
mkdir -p "$BACKUP_DIR"

# 备份核心文件
echo "📦 备份小moe..."
cp bot.py "$BACKUP_DIR/bot_${DATE}.py"
cp knowledge_base_generated.py "$BACKUP_DIR/knowledge_base_${DATE}.py" 2>/dev/null
cp restart_moe.sh "$BACKUP_DIR/restart_moe_${DATE}.sh" 2>/dev/null

# Git提交
git add -A
git commit -m "💾 自动备份 - ${DATE}" 2>/dev/null

echo "✅ 备份完成！"
echo "备份位置: $BACKUP_DIR"
ls -lht "$BACKUP_DIR" | head -5

# 保留最近10次备份
cd "$BACKUP_DIR" && ls -t bot_*.py | tail -n +11 | xargs rm -f 2>/dev/null
cd "$BACKUP_DIR" && ls -t knowledge_base_*.py | tail -n +11 | xargs rm -f 2>/dev/null
