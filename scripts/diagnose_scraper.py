#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
诊断脚本 - 检查JB Hi-Fi网站结构
"""

from playwright.sync_api import sync_playwright
import re
import time

def diagnose_jbhifi():
    print('🔍 诊断 JB Hi-Fi 搜索页面...\n')

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)  # 可视化浏览器，方便调试
        page = browser.new_page()

        # 访问搜索页
        search_url = 'https://www.jbhifi.com.au/search?query=eufy+camera&page=1'
        print(f'访问: {search_url}')
        page.goto(search_url, wait_until='domcontentloaded', timeout=20000)
        time.sleep(3)

        # 获取HTML内容
        content = page.content()

        # 保存完整HTML到文件
        with open('jbhifi_page_dump.html', 'w', encoding='utf-8') as f:
            f.write(content)
        print('✅ 完整HTML已保存到: jbhifi_page_dump.html\n')

        # 尝试多种可能的产品链接模式
        patterns = [
            (r'href="(/products/[^"]+)"', '原始模式: /products/...'),
            (r'href="(https://www.jbhifi.com.au/products/[^"]+)"', '完整URL: https://...'),
            (r'/products/([^"]+)', '任意 /products/ 匹配'),
            (r'<a[^>]*href="([^"]*product[^"]*)"', '包含 product 的链接'),
        ]

        print('测试不同的正则表达式模式:')
        print('-' * 70)

        for pattern, description in patterns:
            matches = re.findall(pattern, content)
            unique_matches = list(set(matches))
            print(f'{description}')
            print(f'  匹配数量: {len(unique_matches)}')
            if unique_matches:
                print(f'  示例: {unique_matches[:3]}')
            print()

        # 检查页面上是否有"eufy"字样
        print('检查页面内容:')
        print('-' * 70)
        eufy_count = content.lower().count('eufy')
        print(f'  "eufy" 出现次数: {eufy_count}')

        # 检查常见的产品卡片元素
        product_cards = [
            'product-card',
            'product-item',
            'product-tile',
            'search-result',
            'ProductCard',
        ]

        print('\n检查产品卡片类名:')
        for card_class in product_cards:
            if card_class in content:
                print(f'  ✅ 找到: {card_class}')
            else:
                print(f'  ❌ 未找到: {card_class}')

        # 尝试使用playwright选择器
        print('\n尝试使用 Playwright 选择器:')
        print('-' * 70)

        selectors = [
            'a[href*="/products/"]',
            'a[href*="product"]',
            '.product-card a',
            '[data-testid*="product"]',
        ]

        for selector in selectors:
            try:
                elements = page.locator(selector).all()
                print(f'{selector}: {len(elements)} 个元素')
                if elements:
                    # 显示前3个链接
                    for i, elem in enumerate(elements[:3]):
                        try:
                            href = elem.get_attribute('href')
                            print(f'    [{i+1}] {href}')
                        except:
                            pass
            except Exception as e:
                print(f'{selector}: 出错 - {e}')

        print('\n按任意键关闭浏览器...')
        input()
        browser.close()

if __name__ == '__main__':
    diagnose_jbhifi()
