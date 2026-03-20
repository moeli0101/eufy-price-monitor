#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
快速测试：eufy搜索功能
"""

from playwright.sync_api import sync_playwright
import re
import time

print('🧪 测试 eufy 搜索功能...\n')

with sync_playwright() as p:
    # 添加反爬虫对策
    browser = p.chromium.launch(
        headless=True,
        args=[
            '--disable-blink-features=AutomationControlled',
            '--no-sandbox',
            '--disable-dev-shm-usage'
        ]
    )

    # 创建页面，设置真实的 User-Agent 和 viewport
    page = browser.new_page(
        user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        viewport={'width': 1920, 'height': 1080}
    )

    # 搜索eufy camera
    search_url = 'https://www.jbhifi.com.au/search?query=eufy+camera&page=1'
    print(f'访问: {search_url}')
    page.goto(search_url, wait_until='domcontentloaded', timeout=30000)
    print('等待页面加载...')
    time.sleep(5)

    content = page.content()
    product_urls = re.findall(r'href="(/products/[^"]+)"', content)
    unique_urls = list(set(product_urls))

    print(f'\n✅ 第1页找到 {len(unique_urls)} 个产品链接')

    if unique_urls:
        print('\n前5个链接:')
        for i, url in enumerate(unique_urls[:5], 1):
            print(f'  {i}. {url}')
    else:
        print('\n❌ 没有找到产品链接')
        print('保存HTML到 test_page.html 进行检查...')
        with open('test_page.html', 'w', encoding='utf-8') as f:
            f.write(content)

    browser.close()

print('\n✅ 测试完成!')
