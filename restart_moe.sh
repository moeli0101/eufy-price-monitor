#!/bin/bash
cd /Users/anker/Desktop/feishu_bot
pkill -9 -f bot.py
sleep 2
nohup python3 -u bot.py > bot_debug.log 2>&1 &
echo "✅ 小moe已重启！"
echo "查看日志: tail -f bot_debug.log"
