#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
新品自动发现脚本
每次运行价格更新后自动扫描 JB Hi-Fi，发现未监控的新产品并添加到列表
"""

from playwright.sync_api import sync_playwright
import json
import time
import random
import re
from pathlib import Path
from product_classifier import classify_product, is_valid_product

SEARCH_TERMS = [
    ('Security Camera', 'eufy security camera'),
    ('Security Camera', 'arlo security camera'),
    ('Security Camera', 'ring security camera'),
    ('Security Camera', 'swann security camera'),
    ('Security Camera', 'tp-link tapo camera'),
    ('Security Camera', 'google nest cam'),
    ('Video Doorbell', 'video doorbell'),
    ('Smart Lock', 'smart lock'),
    ('Baby', 'baby monitor'),
    ('Baby', 'eufy baby'),
    ('Baby', 'momcozy baby'),
    ('Baby', 'nanit baby monitor'),
    ('Baby', 'owlet baby'),
]

ACCESSORY_KEYWORDS = [
    'solar-panel', 'solar panel', 'mount', 'housing', 'charger',
    'bracket', 'cable', 'adapter', 'battery-pack', 'skin', 'case',
    'stand', 'holder', 'siren', 'chime', 'transformer', 'base-station'
]

BRAND_MAP = {
    'eufy': 'eufy', 'arlo': 'Arlo', 'ring': 'Ring',
    'google': 'Google Nest', 'nest': 'Google Nest',
    'tp-link': 'TP-Link', 'tapo': 'TP-Link',
    'swann': 'Swann', 'yale': 'Yale', 'august': 'August',
    'schlage': 'Schlage', 'momcozy': 'Momcozy', 'nanit': 'Nanit',
    'owlet': 'Owlet', 'philips': 'Philips', 'vtech': 'VTech',
}


def is_accessory(url, title=''):
    text = (url + ' ' + title).lower()
    return any(kw in text for kw in ACCESSORY_KEYWORDS)


def detect_brand(title):
    title_lower = title.lower()
    for key, brand in BRAND_MAP.items():
        if key in title_lower:
            return brand
    return 'Other'


def discover_new_products(existing_urls: set) -> list:
    print('🔍 开始扫描 JB Hi-Fi 新品...')
    new_products = []
    seen_urls = set(existing_urls)

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=['--no-sandbox', '--disable-dev-shm-usage', '--disable-blink-features=AutomationControlled']
        )
        page = browser.new_page(
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36',
            viewport={'width': 1920, 'height': 1080}
        )

        for category, term in SEARCH_TERMS:
            search_url = f'https://www.jbhifi.com.au/search?query={term.replace(" ", "+")}'
            try:
                page.goto(search_url, wait_until='domcontentloaded', timeout=30000)
                time.sleep(random.uniform(3, 5))

                content = page.content()
                found_paths = re.findall(r'href="(/products/[^"]+)"', content)
                unique_paths = list(set(found_paths))

                added = 0
                for path in unique_paths:
                    full_url = f'https://www.jbhifi.com.au{path}'

                    if full_url in seen_urls:
                        continue
                    if is_accessory(path):
                        continue

                    detail = browser.new_page()
                    try:
                        detail.goto(full_url, wait_until='domcontentloaded', timeout=20000)
                        time.sleep(1)
                        h1 = detail.locator('h1').first
                        if h1.count() == 0:
                            detail.close()
                            continue
                        title = h1.inner_text().strip()

                        if is_accessory(path, title):
                            detail.close()
                            continue

                        if not is_valid_product(title):
                            detail.close()
                            continue

                        brand = detect_brand(title)
                        cat = classify_product(title, brand)

                        new_products.append({
                            'name': title,
                            'brand': brand,
                            'category': cat,
                            'url': full_url,
                            'channel': 'JB Hi-Fi'
                        })
                        seen_urls.add(full_url)
                        added += 1
                        print(f'  ✅ 新品: [{brand}] {title[:55]}')

                    except Exception:
                        pass
                    finally:
                        detail.close()
                    time.sleep(random.uniform(0.5, 1.5))

                print(f'  [{category}] "{term}": 发现 {added} 个新品')

            except Exception as e:
                print(f'  [{category}] "{term}": 搜索失败 - {e}')

            time.sleep(random.uniform(1, 2))

        browser.close()

    return new_products


def main():
    list_file = Path('product_list_fixed.json')
    if not list_file.exists():
        print('❌ product_list_fixed.json 不存在')
        return

    with open(list_file) as f:
        existing = json.load(f)

    existing_urls = {p['url'] for p in existing}
    print(f'📋 当前监控产品数: {len(existing)}')

    new_products = discover_new_products(existing_urls)

    if not new_products:
        print('✅ 未发现新品，列表已是最新')
        return

    print(f'\n🆕 发现 {len(new_products)} 个新品，正在添加...')
    existing.extend(new_products)

    with open(list_file, 'w', encoding='utf-8') as f:
        json.dump(existing, f, ensure_ascii=False, indent=2)

    print(f'✅ 已更新 product_list_fixed.json：{len(existing)} 个产品（+{len(new_products)}）')

    with open('new_products_found.json', 'w', encoding='utf-8') as f:
        json.dump(new_products, f, ensure_ascii=False, indent=2)
    print(f'📄 新品详情已保存到 new_products_found.json')


if __name__ == '__main__':
    main()
