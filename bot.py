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
from datetime import datetime, timedelta
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
FEISHU_APP_ID = "cli_a93bbc2b02369bd6"
FEISHU_APP_SECRET = "U3Njja1yPuc7Nqqz96Rl4bA74DUGpbl0"
DEEPSEEK_API_KEY = "sk-19b8e5b77ded4709b189ed1fba61cc54"
DEEPSEEK_API_URL = "https://api.deepseek.com/chat/completions"
DEEPSEEK_MODEL = "deepseek-chat"
BITABLE_APP_TOKEN = "CKDJbGdKiagfBpsBl7GccxvZnWd"
BITABLE_TABLE_ID = "tblQ5Ev8TQlmutDS"

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

conversation_history = {}
processed_message_ids = set()
recent_messages = {}

feishu_doc_cache = {}
feishu_docs_list = []
NPI_SHEET_TOKEN = 'ClPssGBvxhmGTStEpB7csINvnGd'
NPI_SHEET_ID = 'uW4AyC'
npi_data_cache = []
price_monitor_cache = []

def load_price_monitor():
    global price_monitor_cache
    if price_monitor_cache:
        return price_monitor_cache
    try:
        resp = requests.get(PRICE_MONITOR_URL, timeout=15, verify=False)
        if resp.status_code == 200:
            data = [p for p in resp.json() if p.get('status') == 'success' and p.get('price')]
            price_monitor_cache = data
            print(f'[价格监控] 已加载 {len(data)} 个产品当前价格')
            return data
    except Exception as e:
        print(f'[价格监控] 加载失败: {e}')
    return []

def search_price(query):
    products = load_price_monitor()
    if not products:
        return '', []
    query_lower = query.lower()
    import re
    stop_words = {'价格', '多少', '钱', '的', '最新', '现在', '目前', '是', '有', '什么', 'price', 'how', 'much', 'current'}
    en_words = [w for w in re.findall(r'[a-zA-Z]{2,}', query_lower) if w not in stop_words]
    cn_words = [w for w in re.findall(r'[\u4e00-\u9fff]{2,}', query_lower) if w not in stop_words]
    model_tokens = re.findall(r'[a-zA-Z]+\d+\w*|\d+[a-zA-Z]+\w*', query_lower)
    all_words = en_words + cn_words + model_tokens

    brand_map = {'ring': 'Ring', 'arlo': 'Arlo', 'tp-link': 'TP-Link', 'tplink': 'TP-Link',
                 'tapo': 'TP-Link', 'swann': 'Swann', 'google': 'Google Nest', 'nest': 'Google Nest',
                 'uniden': 'Uniden', 'eufy': 'eufy'}

    target_brand = None
    for word in en_words:
        if word in brand_map:
            target_brand = brand_map[word]
            break

    scored = []
    for p in products:
        name = p.get('name', '').lower()
        brand = p.get('brand', '')
        score = 0

        if target_brand and brand == target_brand:
            score += 10

        for word in all_words:
            if len(word) >= 2 and word in name:
                score += 5

        if score > 0:
            scored.append((score, p))

    scored.sort(key=lambda x: x[0], reverse=True)
    if not scored:
        return '', []

    max_score = scored[0][0]
    top = [p for score, p in scored if score >= max_score * 0.7][:8]

    lines = []
    for p in top:
        name = p['name']
        brand = p.get('brand', '')
        price = p['price']
        was = p.get('was_price')
        disc = p.get('discount_percent', 0)
        url = p.get('url', '')
        category = p.get('category', '')

        if was and disc:
            line = f"[{brand}] {name} | 💰 ${price} (原${was}, {disc}%off) | {category} | {url}"
        else:
            line = f"[{brand}] {name} | 💰 ${price} | {category} | {url}"
        lines.append(line)

    print(f'[价格查询] "{query}" 命中{len(top)}个产品')
    return '\n'.join(lines), top

def fetch_npi_products():
    global npi_data_cache
    if npi_data_cache:
        return npi_data_cache
    token = get_feishu_token()
    if not token:
        return []
    try:
        headers = ['Owner','PDT','Category','PN','ProductName','系列','Priority','WeeklyUpdate','Cost','MSRP','CR时间','Country']

        def cell_text(cell):
            if cell is None: return ''
            if isinstance(cell, str): return cell.strip()
            if isinstance(cell, list): return ''.join(p.get('text','') for p in cell if isinstance(p,dict)).strip()
            return str(cell).strip()

        products = []
        for sheet_id in ['uW4AyC', 'wr5yoS']:
            resp = requests.get(
                f'https://open.feishu.cn/open-apis/sheets/v2/spreadsheets/{NPI_SHEET_TOKEN}/values/{sheet_id}!A2:P250',
                headers={'Authorization': f'Bearer {token}'},
                params={'valueRenderOption': 'ToString'},
                verify=False, timeout=15
            )
            if resp.status_code != 200:
                continue
            rows = resp.json()['data']['valueRange']['values']
            for row in rows[1:]:
                if not row or not any(row):
                    continue
                p = {}
                for i, h in enumerate(headers):
                    p[h] = cell_text(row[i]) if i < len(row) else ''
                if p.get('PN') and p.get('ProductName') and len(p.get('PN','')) >= 4:
                    msrp = p.get('MSRP', '')
                    try:
                        if msrp and float(msrp) > 10000:
                            continue
                    except:
                        pass
                    products.append(p)
        npi_data_cache = products
        print(f'[产品库] 加载 {len(products)} 个产品（含25年+26年）')
        return products
    except Exception as e:
        print(f'[产品库] 读取失败: {e}')
    return []

def format_cr_date(val):
    if not val:
        return 'TBD'
    try:
        days = int(float(val))
        import datetime
        base = datetime.date(1899, 12, 30)
        d = base + datetime.timedelta(days=days)
        return d.strftime('%Y-%m-%d')
    except:
        return val

def search_npi(query):
    products = fetch_npi_products()
    if not products:
        return '', []
    query_upper = query.upper()
    query_lower = query.lower()
    matched = []
    for p in products:
        pn = p.get('PN', '').upper()
        name = p.get('ProductName', '').lower()
        category = p.get('Category', '').lower()
        series = p.get('系列', '').lower()
        searchable = pn + name + category + series
        score = 0
        import re
        stop_words = {'时间', '的', '是', '有', '什么', '哪些', '多少', '信息', '情况', '怎么', '如何', '产品', 'cr', 'the', 'is', 'in', 'of', 'an'}

        nums = re.findall(r'\d{4,}', query)
        for n in nums:
            if n in pn:
                score += 10

        pn_like = re.findall(r'[A-Z0-9]{2,}', query_upper)
        for token in pn_like:
            if token in stop_words.union({'CR'}):
                continue
            if token == pn or token in pn:
                score += 10
            elif token in searchable.upper():
                score += 5

        en_words = [w for w in re.findall(r'[a-zA-Z]{2,}', query_lower) if w not in stop_words]
        cn_words = [w for w in re.findall(r'[\u4e00-\u9fff]{2,}', query_lower) if w not in stop_words]
        for word in en_words + cn_words:
            if word in searchable.lower():
                score += 5
        if score > 0:
            matched.append((score, p))
    if not matched:
        return '', []
    matched.sort(key=lambda x: x[0], reverse=True)
    max_score = matched[0][0] if matched else 0
    top = [p for score, p in matched if score >= max_score * 0.8][:10]
    lines = []
    for p in top:
        cr = format_cr_date(p['CR时间'])
        line = f"PN: {p['PN']} | {p['ProductName']} | {p['Category']} | MSRP: ${p['MSRP']} | CR时间: {cr} | 优先级: {p['Priority']}"
        if p.get('WeeklyUpdate'):
            line += f"\n  最新动态: {p['WeeklyUpdate'][:100]}"
        lines.append(line)
    result = '\n'.join(lines)
    print(f'[产品库] 查询"{query}"命中 {len(top)} 个产品')
    return result, top

def get_feishu_token():
    try:
        import subprocess
        result = subprocess.run(
            ['python3', '/Users/anker/.claude/skills/managing-feishu/scripts/get_token.py'],
            capture_output=True, text=True, timeout=10
        )
        token = result.stdout.strip().split('\n')[-1].strip()
        if token.startswith('u-'):
            return token
    except Exception as e:
        print(f'[飞书Token] 获取失败: {e}')
    return None

def fetch_bitable_docs():
    global feishu_docs_list
    if feishu_docs_list:
        return feishu_docs_list
    token = get_feishu_token()
    if not token:
        return []
    try:
        resp = requests.get(
            f'https://open.feishu.cn/open-apis/bitable/v1/apps/{BITABLE_APP_TOKEN}/tables/{BITABLE_TABLE_ID}/records',
            headers={'Authorization': f'Bearer {token}'},
            params={'page_size': 100, 'text_field_as_array': 'true'},
            verify=False, timeout=15
        )
        if resp.status_code == 200:
            items = resp.json().get('data', {}).get('items', [])
            docs = []
            for item in items:
                fields = item.get('fields', {})
                def get_text(key):
                    v = fields.get(key, '')
                    if isinstance(v, list):
                        return ''.join(p.get('text', '') for p in v if p.get('type') == 'text' or p.get('type') == 'mention')
                    return str(v)
                category = get_text('分类').strip()
                desc = get_text('文档内容').strip()
                doc_token, doc_type, doc_link = '', 'Docx', ''
                if '链接' in fields:
                    for part in (fields['链接'] if isinstance(fields['链接'], list) else []):
                        if part.get('type') == 'mention' and part.get('token'):
                            doc_token = part['token']
                            doc_type = part.get('mentionType', 'Docx')
                            doc_link = part.get('link', '')
                            break
                if doc_token:
                    docs.append({'category': category, 'desc': desc, 'token': doc_token, 'type': doc_type, 'link': doc_link})
            feishu_docs_list = docs
            print(f'[飞书知识库] 加载 {len(docs)} 篇文档')
            return docs
    except Exception as e:
        print(f'[飞书知识库] 读取失败: {e}')
    return []

def fetch_doc_content(doc_token):
    if doc_token in feishu_doc_cache:
        return feishu_doc_cache[doc_token]
    token = get_feishu_token()
    if not token:
        return ''
    try:
        resp = requests.get(
            f'https://open.feishu.cn/open-apis/docx/v1/documents/{doc_token}/raw_content',
            headers={'Authorization': f'Bearer {token}'},
            verify=False, timeout=15
        )
        if resp.status_code == 200:
            content = resp.json().get('data', {}).get('content', '')[:4000]
            feishu_doc_cache[doc_token] = content
            return content
        else:
            print(f'[飞书文档] 读取失败 {doc_token}: {resp.status_code}')
    except Exception as e:
        print(f'[飞书文档] 读取异常 {doc_token}: {e}')
    return ''

def find_relevant_docs(query):
    docs = fetch_bitable_docs()
    if not docs:
        return []
    keywords = list(query.lower())
    scored = []
    for doc in docs:
        combined = (doc['category'] + doc['desc']).lower()
        score = 0
        for ch in set(query):
            if ch in combined and ch not in ' 的了是在':
                score += 1
        if doc['category'] in query or doc['desc'] in query:
            score += 10
        if any(kw in combined for kw in query.split()):
            score += 5
        if score > 0:
            scored.append((score, doc))
    scored.sort(key=lambda x: x[0], reverse=True)
    top = scored[:2]
    print(f'[RAG] 查询: {query}')
    for score, doc in top:
        print(f'[RAG] 命中: {doc["category"]}/{doc["desc"]} 分数:{score}')
    return [doc for _, doc in top]

def search_feishu_knowledge(query):
    docs = fetch_bitable_docs()
    if not docs:
        return ''
    query_lower = query.lower()
    scored = []
    for doc in docs:
        score = 0
        combined = (doc['category'] + doc['desc']).lower()
        for word in query_lower.split():
            if word in combined:
                score += 2
        if query_lower in combined:
            score += 5
        if score > 0:
            scored.append((score, doc))
    scored.sort(key=lambda x: x[0], reverse=True)
    top = scored[:2]
    if not top:
        return ''
    context = ''
    for score, doc in top:
        print(f'[RAG] 命中文档: {doc["category"]}/{doc["desc"]} (分数:{score})')
        content = fetch_doc_content(doc['token'], doc['type'])
        if content:
            context += f'\n【{doc["category"]} - {doc["desc"]}】\n{content}\n'
    return context

# ==================== 核心功能 ====================

def call_deepseek_api(prompt, user_id='default'):
    try:
        if not user_id or user_id == 'None':
            user_id = 'feishu-bot-user'

        headers = {
            'Authorization': f'Bearer {DEEPSEEK_API_KEY}',
            'Content-Type': 'application/json'
        }

        history = conversation_history.get(user_id, [])

        messages = history + [{'role': 'user', 'content': prompt}]

        data = {
            'model': DEEPSEEK_MODEL,
            'messages': messages,
            'temperature': 0.7,
            'max_tokens': 2000
        }

        response = requests.post(
            DEEPSEEK_API_URL,
            headers=headers,
            json=data,
            verify=False,
            timeout=60
        )

        if response.status_code == 200:
            result = response.json()
            answer = result['choices'][0]['message']['content']

            updated_history = messages + [{'role': 'assistant', 'content': answer}]
            if len(updated_history) > 20:
                updated_history = updated_history[-20:]
            conversation_history[user_id] = updated_history
            print(f'[对话] 用户 {user_id} 对话历史已更新（{len(updated_history)}条）')

            return answer
        else:
            print(f'[DeepSeek] API错误: {response.status_code} - {response.text}')
            return f'抱歉，AI服务暂时不可用（错误码：{response.status_code}）'

    except Exception as e:
        print(f'[DeepSeek] 调用失败: {e}')
        return '抱歉，AI服务连接失败'

def is_persona_question(message):
    """判断是否是询问人设的问题"""
    persona_keywords = [
        '你是谁', '你的主人', '主人是谁', '你叫什么', '自我介绍',
        '你的性格', '你的星座', '你的生日', '你喜欢什么', '你爱吃',
        'ENFP', '双鱼座', 'moe li'
    ]
    message_lower = message.lower()
    return any(keyword in message_lower for keyword in persona_keywords)

def enhance(user_message, user_id='default'):
    if '更新知识库' in user_message or '刷新知识库' in user_message:
        feishu_doc_cache.clear()
        feishu_docs_list.clear()
        npi_data_cache.clear()
        return '知识库缓存已清除，下次提问将重新读取飞书最新内容。'

    persona_block = "你是eufy安防产品知识助手小moe。回答要专业简洁，可以用**加粗**强调关键数据，用数字编号列表，适当使用emoji让回复更生动（比如📦产品信息、📅时间、💰价格、✅确认、⚠️注意），不用#标题，不要过度卖萌。"

    is_persona = is_persona_question(user_message)

    is_price_query = 'jb' in user_message.lower()

    npi_result, npi_matched = search_npi(user_message)
    if npi_result and not is_price_query:
        prompt = f"""{persona_block}

以下是产品库（NPI List）中找到的产品数据：
{npi_result}

用户问题：{user_message}

请直接基于以上数据回答，用**加粗**突出产品名、PN、MSRP、CR时间等关键字段，不要编造任何数据。
注意：这是内部NPI规划数据（建议零售价MSRP），不是JB Hi-Fi实时市场价。如用户需要澳洲实时售价，请提示他们用"JB价格"关键词再问一次。
最后一行附上：参考文档：https://anker-in.feishu.cn/wiki/XdKmwYiM7iz6WCkjzyhcZLtfnxd?sheet=uW4AyC"""
        return call_deepseek_api(prompt, user_id)

    price_result, price_matched = search_price(user_message)
    if price_result:
        prompt = f"""{persona_block}

以下是JB Hi-Fi澳洲站的实时价格数据：
{price_result}

用户问题：{user_message}

请基于以上数据直接回答，用**加粗**突出品牌、产品名、价格，促销产品标注折扣信息。每个产品附上JB Hi-Fi购买链接。
注意：这是JB Hi-Fi澳洲站实时市场价（AUD澳元），不是内部MSRP。"""
        return call_deepseek_api(prompt, user_id)

    relevant_docs = find_relevant_docs(user_message)
    context_parts = []
    links_parts = []
    for doc in relevant_docs:
        content = fetch_doc_content(doc['token'])
        if content:
            context_parts.append(f'【{doc["category"]} - {doc["desc"]}】\n{content}')
        if doc['link']:
            links_parts.append(f'{doc["category"]}/{doc["desc"]}: {doc["link"]}')

    if context_parts:
        context_text = '\n\n'.join(context_parts)
        links_text = '\n'.join(links_parts) if links_parts else ''
        prompt = f"""{persona_block}

以下是内部飞书知识库的相关文档：
{context_text}

用户问题：{user_message}

严格基于以上文档内容回答，不编造文档中没有的信息，用**加粗**突出关键数据。
{('最后附上参考文档：\n' + links_text) if links_text else ''}"""
    elif is_persona:
        prompt = f"""{persona_block}

用户问题：{user_message}

介绍你的人设。"""
    else:
        prompt = f"""{persona_block}

用户问题：{user_message}

内部知识库暂无相关文档，如实告知用户，建议补充相关文档。"""

    return call_deepseek_api(prompt, user_id)

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
    import re
    import traceback
    try:
        message = event.event.message
        sender = event.event.sender

        message_id = message.message_id
        if message_id in processed_message_ids:
            print(f'[跳过] 重复消息ID: {message_id}')
            return
        processed_message_ids.add(message_id)
        if len(processed_message_ids) > 1000:
            processed_message_ids.discard(next(iter(processed_message_ids)))

        chat_id = message.chat_id
        content_str_raw = message.content
        dedup_key = f'{chat_id}:{content_str_raw}'
        now = time.time()
        if dedup_key in recent_messages and now - recent_messages[dedup_key] < 10:
            print(f'[跳过] 10秒内重复内容')
            return
        recent_messages[dedup_key] = now

        content_str = message.content
        print(f'[调试] 原始消息内容: {content_str}')
        content = json.loads(content_str)

        user_message = content.get('text', '').strip()

        # 过滤空消息
        if not user_message:
            print('[调试] 消息为空，跳过')
            return

        # 移除@机器人的部分（兼容多种格式）
        # 格式1: @_user_1（旧格式）
        user_message = user_message.replace('@_user_1', '')
        # 格式2: <at user_id="xxx">小moe</at>（富文本格式）
        user_message = re.sub(r'@\S+\s*', '', user_message)
        user_message = user_message.strip()

        # 过滤清理后为空的消息
        if not user_message:
            print('[调试] 去掉@后消息为空，跳过')
            return

        # 获取用户ID（用于对话历史） - 使用chat_id作为fallback
        try:
            user_id = sender.sender_id.user_id
        except:
            user_id = message.chat_id if hasattr(message, 'chat_id') else 'feishu-user'

        # 确保user_id不为空
        if not user_id or user_id == 'None':
            user_id = 'feishu-user'

        print(f'[收到消息] 用户:{user_id} chat_id:{chat_id} 内容:{user_message}')

        # 生成回复（传递user_id以支持对话记忆）
        reply = enhance(user_message, user_id)

        print(f'[回复] {reply[:100]}...')

        send_reply(message.chat_id, message.message_id, reply, question=user_message)

    except Exception as e:
        print(f'[错误] 处理消息失败: {e}')
        print(traceback.format_exc())

def build_card(question, answer):
    paragraphs = []
    current = []
    for line in answer.split('\n'):
        if line.strip():
            current.append(line)
        else:
            if current:
                paragraphs.append('\n'.join(current))
                current = []
    if current:
        paragraphs.append('\n'.join(current))

    body_elements = []
    for para in paragraphs:
        para = para.strip()
        if not para:
            continue
        body_elements.append({"tag": "markdown", "content": para})

    if not body_elements:
        body_elements.append({"tag": "markdown", "content": answer.strip()})

    body_elements.append({"tag": "hr"})
    body_elements.append({
        "tag": "markdown",
        "content": "🤖 小moe · IoT GTM 助手"
    })

    card = {
        "schema": "2.0",
        "header": {
            "title": {"tag": "plain_text", "content": f"💬 {question}"},
            "template": "blue"
        },
        "body": {
            "elements": body_elements
        }
    }
    return card

def send_reply(chat_id, message_id, text, question=''):
    try:
        card = build_card(question, text)
        request = CreateMessageRequest.builder() \
            .receive_id_type("chat_id") \
            .request_body(
                CreateMessageRequestBody.builder()
                .receive_id(chat_id)
                .msg_type("interactive")
                .content(json.dumps(card))
                .build()
            ) \
            .build()

        response = client.im.v1.message.create(request)

        if not response.success():
            print(f'[卡片发送失败] {response.code}: {response.msg}，降级为文字')
            fallback = CreateMessageRequest.builder() \
                .receive_id_type("chat_id") \
                .request_body(
                    CreateMessageRequestBody.builder()
                    .receive_id(chat_id)
                    .msg_type("text")
                    .content(json.dumps({"text": text}))
                    .build()
                ) \
                .build()
            client.im.v1.message.create(fallback)

    except Exception as e:
        print(f'[错误] 发送消息失败: {e}')

# ==================== 定时任务 ====================
MOE_CHAT_ID = 'oc_3e881be81a557284885a207cccf1b257'
PRICE_MONITOR_URL = 'https://moeli0101.github.io/eufy-price-monitor/price_results_latest.json'
PRICE_HISTORY_URL = 'https://moeli0101.github.io/eufy-price-monitor/price_history.json'
price_snapshot = {}

def send_price_alert_card(eufy_alerts, rival_alerts, date_str):
    elements = []

    if eufy_alerts:
        elements.append({"tag": "markdown", "content": "**📦 eufy 价格变动**"})
        elements.append({"tag": "hr"})
        for a in eufy_alerts:
            line = f"**{a['name']}**\n"
            line += f"💰 ${a['old']} → ${a['new']}  ({'+' if a['change']>0 else ''}{a['change']}%)\n"
            line += f"[查看商品]({a['url']})"
            elements.append({"tag": "markdown", "content": line})

    if rival_alerts:
        if eufy_alerts:
            elements.append({"tag": "hr"})
        elements.append({"tag": "markdown", "content": "**⚠️ 竞品 价格变动**"})
        elements.append({"tag": "hr"})
        for a in rival_alerts:
            line = f"**[{a['brand']}] {a['name']}**\n"
            line += f"💰 ${a['old']} → ${a['new']}  ({'+' if a['change']>0 else ''}{a['change']}%)\n"
            line += f"[查看商品]({a['url']})"
            elements.append({"tag": "markdown", "content": line})

    elements.append({"tag": "hr"})
    elements.append({"tag": "markdown", "content": f"🤖 小moe · JB Hi-Fi 澳洲站 · {date_str}"})

    card = {
        "schema": "2.0",
        "header": {
            "title": {"tag": "plain_text", "content": "📊 JB Hi-Fi 价格变动预警"},
            "template": "orange"
        },
        "body": {"elements": elements}
    }

    try:
        request = CreateMessageRequest.builder() \
            .receive_id_type('chat_id') \
            .request_body(
                CreateMessageRequestBody.builder()
                .receive_id(MOE_CHAT_ID)
                .msg_type('interactive')
                .content(json.dumps(card))
                .build()
            ).build()
        response = client.im.v1.message.create(request)
        if not response.success():
            print(f'[推送失败] {response.code}: {response.msg}')
        else:
            print(f'[推送成功] eufy:{len(eufy_alerts)}条 竞品:{len(rival_alerts)}条')
    except Exception as e:
        print(f'[推送错误] {e}')

def check_price_changes():
    try:
        print('[价格监控] 开始检查...')
        resp = requests.get(PRICE_HISTORY_URL, timeout=15, verify=False)
        if resp.status_code != 200:
            print(f'[价格监控] 历史数据获取失败: {resp.status_code}')
            return
        history_data = resp.json()

        eufy_alerts = []
        rival_alerts = []

        today = datetime.now().strftime('%Y-%m-%d')
        yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')

        has_today = any(
            any(h['date'] == today for h in p.get('price_history', []) if h.get('status') == 'success')
            for p in history_data.values()
        )

        if not has_today:
            print(f'[价格监控] 今天({today})数据还未更新，跳过推送')
            return

        latest_date = today
        prev_date = yesterday
        print(f'[价格监控] 对比 {prev_date} → {latest_date}')

        for key, product in history_data.items():
            history = product.get('price_history', [])
            valid = {h['date']: h for h in history if h.get('status') == 'success' and h.get('price')}

            if latest_date not in valid or prev_date not in valid:
                continue

            latest = valid[latest_date]
            prev = valid[prev_date]

            if latest['price'] == prev['price']:
                continue

            name = product.get('product_name', key)
            brand = product.get('brand', '')
            url = product.get('url', '')
            old_price = prev['price']
            new_price = latest['price']
            change_pct = round((new_price - old_price) / old_price * 100)

            # 过滤脏数据：变动超过35%时，检查前后价格是否连续一致
            if abs(change_pct) > 35:
                sorted_dates = sorted(valid.keys())
                latest_idx = sorted_dates.index(latest_date) if latest_date in sorted_dates else -1
                if latest_idx >= 0:
                    next_dates = sorted_dates[latest_idx + 1:latest_idx + 3]
                    next_prices = [valid[d]['price'] for d in next_dates if d in valid]
                    if not next_prices:
                        print(f'[价格监控] 跳过可疑变动（无后续验证）: {name[:40]} {old_price}→{new_price}')
                        continue
                    if all(abs(p - old_price) / old_price < 0.1 for p in next_prices):
                        print(f'[价格监控] 跳过脏数据（后续价格回归）: {name[:40]} {old_price}→{new_price}')
                        continue

            alert = {
                'name': name,
                'brand': brand,
                'old': old_price,
                'new': new_price,
                'change': change_pct,
                'url': url,
                'date': latest_date
            }

            if brand == 'eufy':
                eufy_alerts.append(alert)
            elif abs(change_pct) >= 5:
                rival_alerts.append(alert)

        if not eufy_alerts and not rival_alerts:
            print(f'[价格监控] {prev_date} → {latest_date} 无价格变化')
            return

        eufy_alerts.sort(key=lambda x: x['change'])
        rival_alerts.sort(key=lambda x: x['change'])

        date_str = f'{prev_date} → {latest_date}'
        send_price_alert_card(eufy_alerts, rival_alerts, date_str)

    except Exception as e:
        print(f'[价格监控] 出错: {e}')

def run_scheduler():
    def weekday_check():
        if datetime.now().weekday() < 5:
            check_price_changes()
    schedule.every().day.at('11:00').do(weekday_check)
    while True:
        schedule.run_pending()
        time.sleep(60)

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

    if not DEEPSEEK_API_KEY:
        print('⚠️  警告：请先配置 DEEPSEEK_API_KEY')
        sys.exit(1)

    print(f'[配置] 飞书App ID: {FEISHU_APP_ID[:10]}...')
    print(f'[配置] DeepSeek已配置: ✅')
    print(f'[配置] 知识库: {len(knowledge_base)} 篇文档')
    print(f'[配置] 产品库: {len(product_database)} 个产品')

    schedule_thread = threading.Thread(target=run_scheduler, daemon=True)
    schedule_thread.start()
    print('[定时任务] 价格监控已启动，工作日11:00推送')

    print('机器人已启动! 等待消息...')
    print('=' * 50)

    docs = fetch_bitable_docs()
    print(f'[预热] 飞书知识库已加载 {len(docs)} 篇文档')
    products = fetch_npi_products()
    print(f'[预热] 产品库已加载 {len(products)} 个产品')
    prices = load_price_monitor()
    print(f'[预热] 价格监控已加载 {len(prices)} 个产品')

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
