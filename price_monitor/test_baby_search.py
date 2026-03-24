#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试eufy baby产品搜索功能
"""

from playwright.sync_api import sync_playwright
import json
import time
import re
from product_classifier import classify_product, is_valid_product

def test_baby_search():
    """测试搜索eufy baby产品"""
    print('🍼 测试eufy baby产品搜索...\n')

    products = []

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,  # 无头模式，更快
            args=[
                '--disable-blink-features=AutomationControlled',
                '--no-sandbox',
                '--disable-dev-shm-usage'
            ]
        )

        # 搜索关键词
        search_terms = ['eufy baby', 'eufy baby monitor', 'eufy breast pump']

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

                for url in unique_urls[:10]:  # 只测试前10个
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

                            print(f'  产品: {title}')

                            # 确认是eufy baby产品
                            if 'eufy' in title_lower and any(kw in title_lower for kw in ['baby', 'breast', 'pump', 'nursing', 'infant', 'monitor']):
                                if is_valid_product(title):
                                    category = classify_product(title, 'eufy')
                                    products.append({
                                        'name': title,
                                        'brand': 'eufy',
                                        'category': category,
                                        'url': full_url,
                                        'channel': 'JB Hi-Fi'
                                    })
                                    print(f'    ✅ 分类为: {category}\n')
                                else:
                                    print(f'    ⚠️  不是有效产品（可能是配件）\n')
                            else:
                                print(f'    ❌ 不符合eufy baby产品条件\n')

                        except Exception as e:
                            print(f'    ❌ 读取产品信息失败: {e}\n')

                        detail_page.close()
                        time.sleep(0.3)

                    except Exception as e:
                        print(f'    ❌ 访问产品页失败: {e}\n')

            except Exception as e:
                print(f'  ⚠️ 搜索失败: {e}\n')

            page.close()
            time.sleep(1)

        browser.close()

    print(f'\n📊 测试结果')
    print(f'=' * 50)
    print(f'共找到 {len(products)} 个有效的eufy baby产品:\n')

    for p in products:
        print(f'  • {p["name"]}')
        print(f'    分类: {p["category"]}')
        print(f'    URL: {p["url"]}\n')

    # 保存到JSON
    with open('test_baby_products.json', 'w', encoding='utf-8') as f:
        json.dump(products, f, ensure_ascii=False, indent=2)

    print(f'✅ 结果已保存到 test_baby_products.json')

if __name__ == '__main__':
    test_baby_search()
