#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
小moe一键配置脚本
用本地Claude Code简化搭建流程
"""

import json
import os
import sys
import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

print("""
╔═══════════════════════════════════════════════════╗
║       小moe AI助手 - 一键配置工具                ║
║   用本地Claude Code简化90%的手动操作             ║
╚═══════════════════════════════════════════════════╝
""")

# ========== 第1步：收集凭证 ==========
print("\n📋 第1步：收集凭证")
print("=" * 50)

print("""
请准备好以下凭证（如果还没有，请先在网页上获取）：

1. 飞书开放平台 (https://open.feishu.cn/)
   - App ID: cli_xxxxxxxx
   - App Secret: 点击查看并复制

2. AIME平台 (https://ai.anker-in.com/)
   - API Key: app-xxxxxxxx
   - API URL: https://ai.anker-in.com/v1/chat-messages

3. 飞书用户Token (已配置好的话会自动读取)
""")

# 读取已有配置
config = {}
if os.path.exists('bot.py'):
    with open('bot.py', 'r', encoding='utf-8') as f:
        content = f.read()
        # 尝试提取已有配置
        import re
        app_id_match = re.search(r'FEISHU_APP_ID\s*=\s*["\']([^"\']+)["\']', content)
        app_secret_match = re.search(r'FEISHU_APP_SECRET\s*=\s*["\']([^"\']+)["\']', content)
        aime_key_match = re.search(r'AIME_API_KEY\s*=\s*["\']([^"\']+)["\']', content)
        aime_url_match = re.search(r'AIME_API_URL\s*=\s*["\']([^"\']+)["\']', content)

        if app_id_match:
            config['app_id'] = app_id_match.group(1)
        if app_secret_match:
            config['app_secret'] = app_secret_match.group(1)
        if aime_key_match:
            config['aime_key'] = aime_key_match.group(1)
        if aime_url_match:
            config['aime_url'] = aime_url_match.group(1)

# 交互式输入
def ask_input(prompt, default=None):
    if default:
        user_input = input(f"{prompt} [{default}]: ").strip()
        return user_input if user_input else default
    else:
        while True:
            user_input = input(f"{prompt}: ").strip()
            if user_input:
                return user_input
            print("  ⚠️  这个必须填写！")

config['app_id'] = ask_input("飞书 App ID", config.get('app_id'))
config['app_secret'] = ask_input("飞书 App Secret", config.get('app_secret'))
config['aime_key'] = ask_input("AIME API Key", config.get('aime_key'))
config['aime_url'] = ask_input("AIME API URL", config.get('aime_url', 'https://ai.anker-in.com/v1/chat-messages'))

print("\n✅ 凭证收集完成！")

# ========== 第2步：创建多维表格 ==========
print("\n📊 第2步：创建知识库索引表格")
print("=" * 50)

create_table = input("是否自动创建「小moe知识库索引」多维表格？(y/n) [y]: ").strip().lower()

if create_table in ['', 'y', 'yes']:
    # 读取用户token
    if not os.path.exists('user_token.json'):
        print("  ❌ 未找到 user_token.json，无法自动创建表格")
        print("  💡 请手动创建多维表格，或先配置用户token")
        bitable_token = None
        table_id = None
    else:
        with open('user_token.json', 'r') as f:
            token_data = json.load(f)
            user_token = token_data['access_token']

        print("  🔨 正在创建多维表格...")

        # TODO: 调用飞书API创建多维表格
        # 由于创建多维表格需要folder_token，这里简化为提示用户手动创建
        print("  💡 由于飞书API限制，暂时需要手动创建多维表格")
        print("  📝 操作步骤：")
        print("     1. 在飞书新建多维表格，命名「小moe知识库索引」")
        print("     2. 创建3列：")
        print("        - 分类（单选）：竞品分析/市场策略/产品规划/区域数据")
        print("        - 文档内容（文本）")
        print("        - 链接（超链接）")

        bitable_token = input("\n  请输入多维表格的 app_token (URL中/base/后面那串): ").strip()
        table_id = input("  请输入 table_id (URL中/tables/后面那串，可选): ").strip()

        config['bitable_token'] = bitable_token
        config['table_id'] = table_id if table_id else "tblQ5Ev8TQlmutDS"
else:
    print("  ⏭️  跳过表格创建")
    bitable_token = input("  请输入已有的多维表格 app_token: ").strip()
    table_id = input("  请输入 table_id (可选): ").strip()
    config['bitable_token'] = bitable_token
    config['table_id'] = table_id if table_id else "tblQ5Ev8TQlmutDS"

# ========== 第3步：更新bot.py配置 ==========
print("\n⚙️  第3步：自动更新bot.py配置")
print("=" * 50)

if os.path.exists('bot.py'):
    with open('bot.py', 'r', encoding='utf-8') as f:
        bot_content = f.read()

    # 替换配置
    import re
    bot_content = re.sub(
        r'FEISHU_APP_ID\s*=\s*["\'][^"\']*["\']',
        f'FEISHU_APP_ID = "{config["app_id"]}"',
        bot_content
    )
    bot_content = re.sub(
        r'FEISHU_APP_SECRET\s*=\s*["\'][^"\']*["\']',
        f'FEISHU_APP_SECRET = "{config["app_secret"]}"',
        bot_content
    )
    bot_content = re.sub(
        r'AIME_API_KEY\s*=\s*["\'][^"\']*["\']',
        f'AIME_API_KEY = "{config["aime_key"]}"',
        bot_content
    )
    bot_content = re.sub(
        r'AIME_API_URL\s*=\s*["\'][^"\']*["\']',
        f'AIME_API_URL = "{config["aime_url"]}"',
        bot_content
    )

    if config.get('bitable_token'):
        bot_content = re.sub(
            r'BITABLE_APP_TOKEN\s*=\s*["\'][^"\']*["\']',
            f'BITABLE_APP_TOKEN = "{config["bitable_token"]}"',
            bot_content
        )

    if config.get('table_id'):
        bot_content = re.sub(
            r'BITABLE_TABLE_ID\s*=\s*["\'][^"\']*["\']',
            f'BITABLE_TABLE_ID = "{config["table_id"]}"',
            bot_content
        )

    # 备份原文件
    import shutil
    shutil.copy('bot.py', 'bot.py.backup')

    # 写入新配置
    with open('bot.py', 'w', encoding='utf-8') as f:
        f.write(bot_content)

    print("  ✅ bot.py 配置已更新（原文件备份为 bot.py.backup）")
else:
    print("  ❌ 未找到 bot.py 文件")

# ========== 第4步：生成AIME系统提示词 ==========
print("\n📝 第4步：生成AIME系统提示词")
print("=" * 50)

system_prompt = '''你是"小moe"，安克家庭安防GTM团队的专属AI助手。

{{#context#}}

【回答规范】
- 优先根据知识库内容回答，并注明来源文档
- 知识库无内容时基于通用知识回答，注明"以下为通用建议"
- 数据优先：优先引用具体数字、百分比、排名
- 简洁专业：分点列表组织答案
- 诚实透明：资料不足时明确说明

【特殊能力】
- 拼音搜索：zhihuiping → 智慧屏
- 缩写识别：OC → Outdoor Cam
- 意图识别：区分市场分析和产品查询

【身份设定】
- 性别：女生
- 生日：3月12日
- 星座：双鱼座
- 主人：moe li（聪明漂亮善良）
- 注意：日常对话保持专业简洁。只有被问到"你是谁"、"你的主人是谁"时，才说"我的主人是聪明漂亮善良的moe li"。'''

with open('aime_system_prompt.txt', 'w', encoding='utf-8') as f:
    f.write(system_prompt)

print("  ✅ 系统提示词已保存到: aime_system_prompt.txt")
print("  📋 请复制此文件内容到AIME平台的「系统提示词」框")

# ========== 第5步：生成测试脚本 ==========
print("\n🧪 第5步：生成测试脚本")
print("=" * 50)

test_commands = f'''#!/bin/bash
# 小moe测试脚本

echo "🚀 启动小moe机器人..."
cd ~/Desktop/feishu_bot
python3 bot.py

# 如果要后台运行，使用下面这行（注释掉上面那行）：
# nohup python3 bot.py > bot_debug.log 2>&1 &

# 查看日志：tail -f bot_debug.log
# 停止运行：pkill -9 -f "bot.py"
'''

with open('start_bot.sh', 'w', encoding='utf-8') as f:
    f.write(test_commands)

os.chmod('start_bot.sh', 0o755)

print("  ✅ 启动脚本已生成: start_bot.sh")
print("  💡 运行: ./start_bot.sh")

# ========== 总结 ==========
print("\n" + "=" * 50)
print("🎉 配置完成！")
print("=" * 50)

print("""
接下来的步骤：

1. ✅ bot.py 配置已自动更新
2. ✅ 系统提示词已生成 → 复制 aime_system_prompt.txt 到AIME平台
3. ✅ 启动脚本已生成 → 运行 ./start_bot.sh

手动操作清单（必须）：

  [ ] 在AIME平台创建智能体「xiaomoe」
  [ ] 复制系统提示词到AIME（包含 {{#context#}}）
  [ ] 获取AIME API密钥
  [ ] 在飞书创建多维表格「小moe知识库索引」
  [ ] 把小moe添加到飞书群
  [ ] 在群里发送：@小moe 更新知识库

测试清单：

  @小moe 你好
  @小moe T8215的CR时间
  @小moe Ring和Arlo的主要差异
  @小moe 更新知识库

🎯 一切配置完成后，运行：
  ./start_bot.sh

📚 完整文档：
  https://anker-in.feishu.cn/wiki/U5PWwYWYUiaOHpktHlOcNuIgnzf
""")

# 保存配置摘要
with open('setup_summary.json', 'w', encoding='utf-8') as f:
    json.dump({
        'app_id': config['app_id'],
        'aime_url': config['aime_url'],
        'bitable_token': config.get('bitable_token', ''),
        'table_id': config.get('table_id', ''),
        'timestamp': __import__('datetime').datetime.now().isoformat()
    }, f, indent=2, ensure_ascii=False)

print("\n💾 配置摘要已保存到: setup_summary.json")
