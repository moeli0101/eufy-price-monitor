#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试搜索所有品牌的baby产品
"""

from playwright.sync_api import sync_playwright
import json
import time
import re
from product_classifier import classify_product, is_valid_product

def test_baby_search():
    """测试搜索所有品牌baby产品"""
    print('🍼 测试搜索所有品牌baby产品...\n')

    products = []

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--no-sandbox',
                '--disable-dev-shm-usage'
            ]
        )

        # 搜索关键词
        search_terms = [
            'baby monitor',
            'breast pump',
            'momcozy baby',
            'nanit baby monitor',
            'owlet baby',
            'eufy baby'
        ]

        for term in search_terms:
            print(f'🔍 搜索: {term}')
            page = browser.new_page(
                user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                viewport={'width': 1920, 'height': 1080}
            )

            try:
                search_url = f'https://www.jbhifi.com.au/search?query={term.replace(" ", "+")}'
                page.goto(search_url, wait_until='domcontentloaded', timeout=30000)
                time.sleep(5)

                content = page.content()
                product_urls = re.findall(r'href="(/products/[^"]+)"', content)
                unique_urls = list(set(product_urls))

                print(f'  找到 {len(unique_urls)} 个产品链接\n')

                for url in unique_urls[:15]:  # 测试前15个
                    full_url = f'https://www.jbhifi.com.au{url}'

                    # 避免重复
                    if any(p['url'] == full_url for p in products):
                        continue

                    try:
                        detail_page = browser.new_page()
                        detail_page.goto(full_url, timeout=12000)
                        time.sleep(1)

                        try:
                            title = detail_page.locator('h1').first.inner_text()
                            title_lower = title.lower()

                            # 确认是baby相关产品
                            if any(kw in title_lower for kw in ['baby', 'breast', 'pump', 'nursing', 'infant', 'monitor', 'momcozy', 'nanit', 'owlet']):
                                if is_valid_product(title):
                                    category = classify_product(title)

                                    # 识别品牌
                                    brand = 'Other'
                                    if 'eufy' in title_lower:
                                        brand = 'eufy'
                                    elif 'momcozy' in title_lower:
                                        brand = 'Momcozy'
                                    elif 'nanit' in title_lower:
                                        brand = 'Nanit'
                                    elif 'owlet' in title_lower:
                                        brand = 'Owlet'
                                    elif 'philips' in title_lower:
                                        brand = 'Philips'
                                    elif 'vtech' in title_lower:
                                        brand = 'VTech'

                                    # 只添加Baby类别
                                    if category == 'Baby':
                                        products.append({
                                            'name': title,
                                            'brand': brand,
                                            'category': category,
                                            'url': full_url,
                                            'channel': 'JB Hi-Fi'
                                        })
                                        print(f'  ✅ {brand} - {title}')
                                    else:
                                        print(f'  ⚠️  分类为 {category} - {title}')

                        except Exception as e:
                            pass

                        detail_page.close()
                        time.sleep(0.3)

                    except:
                        pass

            except Exception as e:
                print(f'  ⚠️ 搜索失败: {e}')

            page.close()
            time.sleep(1)
            print()

        browser.close()

    print(f'\n📊 测试结果')
    print(f'=' * 80)
    print(f'共找到 {len(products)} 个Baby产品:\n')

    # 按品牌分组
    from collections import defaultdict
    by_brand = defaultdict(list)
    for p in products:
        by_brand[p['brand']].append(p)

    for brand, prods in sorted(by_brand.items()):
        print(f'\n【{brand}】({len(prods)}款):')
        for p in prods:
            print(f'  • {p["name"]}')

    # 保存
    with open('test_all_baby_products.json', 'w', encoding='utf-8') as f:
        json.dump(products, f, ensure_ascii=False, indent=2)

    print(f'\n✅ 结果已保存到 test_all_baby_products.json')

if __name__ == '__main__':
    test_baby_search()
