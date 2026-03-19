#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
小moe - IoT GTM AI助手
"""

# 必须在所有import之前设置环境变量
import os
os.environ['PYTHONHTTPSVERIFY'] = '0'
os.environ['WEBSOCKET_CLIENT_CA_BUNDLE'] = ''
os.environ['CURL_CA_BUNDLE'] = ''
os.environ['REQUESTS_CA_BUNDLE'] = ''

import json
import sys
import time
import requests
import urllib3
import ssl
from datetime import datetime
import schedule
import threading

# 禁用SSL验证
ssl._create_default_https_context = ssl._create_unverified_context
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Patch websockets库禁用SSL验证
import websockets
_original_connect = websockets.connect

def _patched_connect(*args, **kwargs):
    # 强制禁用SSL验证
    if 'ssl' not in kwargs or kwargs.get('ssl') is not False:
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        kwargs['ssl'] = ssl_context
    return _original_connect(*args, **kwargs)

websockets.connect = _patched_connect

# 飞书SDK
import lark_oapi as lark
from lark_oapi.api.im.v1 import *

# ==================== 配置区域 ====================
# ⚠️ 请修改这些配置！
FEISHU_APP_ID = "cli_a93bbc2b02369bd6"  # 从飞书开放平台获取
FEISHU_APP_SECRET = "U3Njja1yPuc7Nqqz96Rl4bA74DUGpbl0"  # 从飞书开放平台获取
AIME_API_KEY = "app-BUXRqbg1Z98MIvMqIi5BA8Bj"  # 从 https://ai.anker-in.com/ 获取
AIME_API_URL = "https://ai.anker-in.com/v1/chat-messages"  # AIME API地址
BITABLE_APP_TOKEN = "CKDJbGdKiagfBpsBl7GccxvZnWd"  # 知识库多维表格token
BITABLE_TABLE_ID = "tblQ5Ev8TQlmutDS"  # 知识库表格ID

# 日报配置（已禁用）
# DAILY_REPORT_TIME = "08:00"
# DAILY_REPORT_CHAT_ID = ""

# ==================== 初始化 ====================

# 创建飞书客户端
client = lark.Client.builder() \
    .app_id(FEISHU_APP_ID) \
    .app_secret(FEISHU_APP_SECRET) \
    .build()

# 加载知识库（如果存在）
knowledge_base = {}
if os.path.exists('knowledge_base_generated.py'):
    try:
        from knowledge_base_generated import KNOWLEDGE_BASE
        knowledge_base = KNOWLEDGE_BASE
        print(f'[知识库] 成功导入生成的知识库，共 {len(knowledge_base)} 篇文档')
    except Exception as e:
        print(f'[知识库] 导入失败: {e}')

# 加载产品库（如果存在）
product_database = {}
if os.path.exists('product_database.json'):
    try:
        with open('product_database.json', 'r', encoding='utf-8') as f:
            product_database = json.load(f)
        print(f'[产品库] 已加载 {len(product_database)} 个产品')
    except Exception as e:
        print(f'[产品库] 加载失败: {e}')

# ==================== 核心功能 ====================

def call_aime_api(messages, user_query):
    """调用AIME API"""
    try:
        headers = {
            'Authorization': f'Bearer {AIME_API_KEY}',
            'Content-Type': 'application/json'
        }

        data = {
            'inputs': {},
            'query': user_query,
            'response_mode': 'blocking',
            'conversation_id': '',
            'user': 'feishu-bot',
            'files': []
        }

        response = requests.post(
            AIME_API_URL,
            headers=headers,
            json=data,
            verify=False,
            timeout=30
        )

        if response.status_code == 200:
            result = response.json()
            return result.get('answer', '抱歉，我没有理解您的问题')
        else:
            print(f'[AIME] API错误: {response.status_code}')
            return f'抱歉，AI服务暂时不可用（错误码：{response.status_code}）'

    except Exception as e:
        print(f'[AIME] 调用失败: {e}')
        return '抱歉，AI服务连接失败'

def enhance(user_message):
    """增强回复 - 添加知识库和产品库支持"""

    # 1. 检查是否是更新知识库命令
    if '更新知识库' in user_message or '刷新知识库' in user_message:
        return handle_update_knowledge_base()

    # 2. 检查产品库
    product_info = search_product(user_message)
    if product_info:
        # 如果找到产品，直接返回产品信息
        return format_product_info(product_info)

    # 3. 检查知识库
    kb_context = search_knowledge_base(user_message)
    if kb_context:
        # 有知识库内容，增强prompt
        prompt = f"""你是eufy产品知识助手"小moe"（女生，3月12日生日，双鱼座，主人是moe li）。

以下是从知识库找到的相关资料：
{kb_context}

请基于以上资料回答用户问题：{user_message}

要求：
1. 优先使用知识库资料
2. 引用时注明来源
3. 如果资料不足，可以说明
4. 保持专业简洁"""

        return call_aime_api([], prompt)

    # 4. 没有知识库，正常回复
    prompt = f"""你是eufy产品知识助手"小moe"（女生，3月12日生日，双鱼座，主人是moe li）。

用户问题：{user_message}

注意：在日常对话中保持专业简洁。只有在被问到"你是谁"、"你的主人是谁"等相关问题时，才可以说"我的主人是聪明漂亮善良的moe li"。"""

    return call_aime_api([], prompt)

def search_product(query):
    """搜索产品库"""
    if not product_database:
        return None

    query_lower = query.lower()

    # 搜索产品代码或名称
    for product_id, product_info in product_database.items():
        if product_id.lower() in query_lower:
            return product_info
        if product_info.get('name', '').lower() in query_lower:
            return product_info

    return None

def format_product_info(product_info):
    """格式化产品信息"""
    result = f"""📦 产品信息【{product_info.get('code', 'N/A')}】

• 产品名称: {product_info.get('name', 'N/A')}
• CR时间: {product_info.get('cr_date', 'N/A')}
• 建议零售价: {product_info.get('price', 'N/A')}
• 优先级: {product_info.get('priority', 'N/A')}
• 备注: {product_info.get('notes', '无')}
"""
    return result

def search_knowledge_base(query):
    """搜索知识库"""
    if not knowledge_base:
        return None

    # 简单的关键词匹配
    relevant_docs = []
    query_keywords = query.lower().split()

    for doc_name, doc_content in knowledge_base.items():
        content_lower = doc_content.lower()
        # 计算匹配度
        matches = sum(1 for keyword in query_keywords if keyword in content_lower)
        if matches > 0:
            relevant_docs.append({
                'name': doc_name,
                'content': doc_content[:1000],  # 只取前1000字
                'score': matches
            })

    if not relevant_docs:
        return None

    # 按匹配度排序，取前2篇
    relevant_docs.sort(key=lambda x: x['score'], reverse=True)
    top_docs = relevant_docs[:2]

    # 格式化返回
    context = ""
    for doc in top_docs:
        context += f"\n【{doc['name']}】\n{doc['content']}\n"

    return context

def handle_update_knowledge_base():
    """处理更新知识库命令"""
    # TODO: 实现从飞书多维表格读取文档
    # 这里需要实现读取飞书多维表格并生成knowledge_base_generated.py
    return """[更新] 知识库更新功能需要配置多维表格。

如需更新知识库，请：
1. 确保 BITABLE_APP_TOKEN 已配置
2. 多维表格已添加新文档
3. 运行更新脚本

或联系管理员协助更新。"""

# ==================== 飞书消息处理 ====================

def handle_message(event):
    """处理接收到的消息"""
    try:
        message = event.event.message
        content_str = message.content
        content = json.loads(content_str)

        user_message = content.get('text', '').strip()

        # 过滤空消息
        if not user_message:
            return

        # 移除@机器人的部分
        user_message = user_message.replace('@_user_1', '').strip()

        print(f'[收到消息] {user_message}')

        # 生成回复
        reply = enhance(user_message)

        print(f'[回复] {reply[:100]}...')

        # 发送回复
        send_reply(message.chat_id, message.message_id, reply)

    except Exception as e:
        print(f'[错误] 处理消息失败: {e}')

def send_reply(chat_id, message_id, text):
    """发送回复"""
    try:
        request = CreateMessageRequest.builder() \
            .receive_id_type("chat_id") \
            .request_body(
                CreateMessageRequestBody.builder()
                .receive_id(chat_id)
                .msg_type("text")
                .content(json.dumps({"text": text}))
                .reply_in_thread(False)
                .build()
            ) \
            .build()

        response = client.im.v1.message.create(request)

        if not response.success():
            print(f'[发送失败] {response.code}: {response.msg}')

    except Exception as e:
        print(f'[错误] 发送消息失败: {e}')

# ==================== 定时任务 ====================
# 日报功能已禁用 - 如需启用请重新配置

# def send_daily_report():
#     """发送每日报告"""
#     pass

# def schedule_tasks():
#     """设置定时任务"""
#     pass

# ==================== 主程序 ====================

def main():
    """主程序"""
    print('=' * 50)
    print('小moe 启动中...')
    print('=' * 50)

    # 检查配置
    if FEISHU_APP_ID == "你的飞书App ID":
        print('⚠️  警告：请先配置 FEISHU_APP_ID 和 FEISHU_APP_SECRET')
        print('请编辑 bot.py 文件，填入你的飞书凭证')
        sys.exit(1)

    if AIME_API_KEY == "你的AIME API Key":
        print('⚠️  警告：请先配置 AIME_API_KEY')
        print('请编辑 bot.py 文件，填入你的AIME API Key')
        sys.exit(1)

    print(f'[配置] 飞书App ID: {FEISHU_APP_ID[:10]}...')
    print(f'[配置] AIME已配置: {"✅" if AIME_API_KEY != "你的AIME API Key" else "❌"}')
    print(f'[配置] 知识库: {len(knowledge_base)} 篇文档')
    print(f'[配置] 产品库: {len(product_database)} 个产品')

    # 定时任务已禁用
    # schedule_thread = threading.Thread(target=schedule_tasks, daemon=True)
    # schedule_thread.start()

    print('机器人已启动! 等待消息...')
    print('=' * 50)

    # 创建WebSocket消息处理器
    handler = lark.EventDispatcherHandler.builder(
        "", ""  # 这里留空，使用 APP_ID 和 APP_SECRET
    ).register_p2_im_message_receive_v1(
        handle_message
    ).build()

    # 创建并启动WebSocket客户端
    cli = lark.ws.Client(FEISHU_APP_ID, FEISHU_APP_SECRET, event_handler=handler)
    cli.start()

if __name__ == '__main__':
    main()
