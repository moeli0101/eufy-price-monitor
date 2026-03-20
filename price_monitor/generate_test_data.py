#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
生成测试数据用于促销日历
"""

import json
from datetime import datetime, timedelta
import random

# 读取现有的价格数据
with open('price_results_latest.json', 'r', encoding='utf-8') as f:
    products = json.load(f)

print(f'📦 加载了 {len(products)} 个产品')

# 生成历史数据
history = {}
today = datetime.now()

for product in products:
    if product['status'] != 'success' or not product.get('price'):
        continue

    # 生成产品ID
    name_clean = product['name'].lower()
    for char in [' ', '-', '/', '(', ')', ',', '.', '&']:
        name_clean = name_clean.replace(char, '_')
    while '__' in name_clean:
        name_clean = name_clean.replace('__', '_')
    product_id = f"{product['brand'].lower()}_{name_clean[:60].strip('_')}"

    current_price = product['price']

    # 生成过去30天的价格历史
    price_history = []
    for days_ago in range(30, -1, -1):
        date = today - timedelta(days=days_ago)
        date_str = date.strftime('%Y-%m-%d')

        # 80%概率正常价格，20%概率促销
        is_sale = random.random() < 0.2

        if is_sale:
            # 促销价格（打7-9折）
            discount = random.randint(10, 30)
            price = round(current_price * (1 - discount/100), 2)
            original = current_price
        else:
            # 正常价格（可能有小幅波动）
            price = current_price
            original = current_price

        price_history.append({
            'date': date_str,
            'price': price,
            'original_price': original,
            'is_on_sale': is_sale,
            'discount_percentage': round((original - price) / original * 100, 1) if is_sale else 0
        })

    history[product_id] = {
        'product_name': product['name'],
        'brand': product['brand'],
        'category': product.get('category', 'Security Camera'),
        'url': product.get('url', ''),
        'channel': product.get('channel', 'JB Hi-Fi'),
        'price_history': price_history
    }

# 保存历史数据
with open('price_history.json', 'w', encoding='utf-8') as f:
    json.dump(history, f, ensure_ascii=False, indent=2)

print(f'✅ 已生成 price_history.json ({len(history)} 个产品)')

# 生成促销数据
promotions = {}
for product_id, product_data in history.items():
    # 找最新的促销
    latest_sale = None
    for record in reversed(product_data['price_history']):
        if record['is_on_sale']:
            latest_sale = record
            break

    if latest_sale:
        promotions[product_id] = {
            'product_name': product_data['product_name'],
            'brand': product_data['brand'],
            'category': product_data['category'],
            'url': product_data['url'],
            'current_price': latest_sale['price'],
            'original_price': latest_sale['original_price'],
            'discount_percentage': latest_sale['discount_percentage'],
            'start_date': latest_sale['date'],
            'last_seen': today.strftime('%Y-%m-%d')
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
print(f'\n📊 统计：')
print(f'  - 历史记录: {len(history)} 个产品')
print(f'  - 当前促销: {len(promotions)} 个产品')
print(f'  - 数据时间范围: 过去30天')
