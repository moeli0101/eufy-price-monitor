#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
用真实抓取数据生成历史记录
"""

import json
from datetime import datetime

# 读取真实的价格数据
with open('price_results_latest.json', 'r', encoding='utf-8') as f:
    products = json.load(f)

print(f'📦 加载了 {len(products)} 个产品')

# 生成历史数据
history = {}
scraped_date = None

for product in products:
    if product['status'] != 'success' or not product.get('price'):
        continue

    # 获取抓取日期
    if not scraped_date and product.get('scraped_at'):
        scraped_date = product['scraped_at'].split('T')[0]

    date_str = scraped_date or datetime.now().strftime('%Y-%m-%d')

    # 生成产品ID
    name_clean = product['name'].lower()
    for char in [' ', '-', '/', '(', ')', ',', '.', '&']:
        name_clean = name_clean.replace(char, '_')
    while '__' in name_clean:
        name_clean = name_clean.replace('__', '_')
    product_id = f"{product['brand'].lower()}_{name_clean[:60].strip('_')}"

    current_price = product['price']
    was_price = product.get('was_price', current_price)

    # 是否促销
    is_sale = was_price > current_price
    discount = 0
    if is_sale:
        discount = round((was_price - current_price) / was_price * 100, 1)

    # 创建历史记录（目前只有1天的数据）
    history[product_id] = {
        'product_name': product['name'],
        'brand': product['brand'],
        'category': product.get('category', 'Security Camera'),
        'url': product.get('url', ''),
        'channel': product.get('channel', 'JB Hi-Fi'),
        'price_history': [
            {
                'date': date_str,
                'price': current_price,
                'original_price': was_price,
                'is_on_sale': is_sale,
                'discount_percentage': discount
            }
        ]
    }

# 保存历史数据
with open('price_history.json', 'w', encoding='utf-8') as f:
    json.dump(history, f, ensure_ascii=False, indent=2)

print(f'✅ 已生成 price_history.json ({len(history)} 个产品)')
print(f'📅 数据日期: {date_str}')

# 生成促销数据
promotions = {}
for product_id, product_data in history.items():
    latest = product_data['price_history'][0]

    if latest['is_on_sale']:
        promotions[product_id] = {
            'product_name': product_data['product_name'],
            'brand': product_data['brand'],
            'category': product_data['category'],
            'url': product_data['url'],
            'current_price': latest['price'],
            'original_price': latest['original_price'],
            'discount_percentage': latest['discount_percentage'],
            'start_date': latest['date'],
            'last_seen': latest['date']
        }

with open('promotions.json', 'w', encoding='utf-8') as f:
    json.dump(promotions, f, ensure_ascii=False, indent=2)

print(f'✅ 已生成 promotions.json ({len(promotions)} 个促销)')

# 复制到docs目录
import shutil
shutil.copy('price_history.json', 'docs/price_history.json')
shutil.copy('promotions.json', 'docs/promotions.json')
shutil.copy('price_results_latest.json', 'docs/price_results_latest.json')

print(f'✅ 已复制数据文件到 docs/ 目录')
print(f'\n⚠️  注意：目前只有 {date_str} 一天的数据')
print(f'    需要每天运行抓取脚本才能积累历史趋势')
