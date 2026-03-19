#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
抓取Google Nest展陈相关信息
"""

from playwright.sync_api import sync_playwright
import json
import time
from datetime import datetime

def scrape_google_nest_info():
    """抓取Google Nest相关信息"""

    results = {
        'scraped_at': datetime.now().isoformat(),
        'sources': []
    }

    with sync_playwright() as p:
        # 使用与价格抓取相同的反爬虫策略
        browser = p.chromium.launch(
            headless=True,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--no-sandbox',
                '--disable-dev-shm-usage'
            ]
        )

        page = browser.new_page(
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            viewport={'width': 1920, 'height': 1080}
        )

        # 1. 抓取Best Buy的Google Nest页面
        print('📱 抓取Best Buy Google Nest页面...')
        try:
            page.goto('https://www.bestbuy.com/site/searchpage.jsp?st=google+nest',
                     wait_until='domcontentloaded', timeout=30000)
            time.sleep(3)

            # 提取页面标题和描述
            title = page.title()

            # 提取产品列表
            products = []
            try:
                product_elements = page.locator('.sku-item').all()
                for elem in product_elements[:10]:  # 只取前10个
                    try:
                        name = elem.locator('.sku-title').inner_text()
                        price_elem = elem.locator('.priceView-customer-price span')
                        price = price_elem.inner_text() if price_elem.count() > 0 else 'N/A'
                        products.append({'name': name, 'price': price})
                    except:
                        pass
            except Exception as e:
                print(f'  产品列表提取失败: {e}')

            results['sources'].append({
                'source': 'Best Buy',
                'url': 'https://www.bestbuy.com/site/searchpage.jsp?st=google+nest',
                'title': title,
                'products_found': len(products),
                'sample_products': products[:3]
            })

            print(f'  ✅ Best Buy: 找到 {len(products)} 个产品')

        except Exception as e:
            print(f'  ❌ Best Buy 抓取失败: {e}')
            results['sources'].append({
                'source': 'Best Buy',
                'status': 'failed',
                'error': str(e)
            })

        # 2. 抓取Google Store
        print('\\n🏪 抓取Google Store...')
        try:
            page.goto('https://store.google.com/us/category/connected_home',
                     wait_until='domcontentloaded', timeout=30000)
            time.sleep(3)

            title = page.title()

            # 尝试提取产品信息
            page_text = page.inner_text('body')
            nest_mentions = page_text.lower().count('nest')

            results['sources'].append({
                'source': 'Google Store',
                'url': 'https://store.google.com/us/category/connected_home',
                'title': title,
                'nest_mentions': nest_mentions,
                'note': '页面需要JavaScript渲染，可能需要更复杂的抓取'
            })

            print(f'  ✅ Google Store: 页面加载成功，提到"nest" {nest_mentions}次')

        except Exception as e:
            print(f'  ❌ Google Store 抓取失败: {e}')
            results['sources'].append({
                'source': 'Google Store',
                'status': 'failed',
                'error': str(e)
            })

        # 3. 搜索零售设计相关信息
        print('\\n🔍 搜索零售设计信息...')
        try:
            # 使用Google搜索"google nest best buy display"
            search_query = 'google+nest+best+buy+display+retail'
            page.goto(f'https://www.google.com/search?q={search_query}',
                     wait_until='domcontentloaded', timeout=30000)
            time.sleep(2)

            # 提取搜索结果标题
            search_results = []
            try:
                result_elements = page.locator('.g').all()
                for elem in result_elements[:10]:
                    try:
                        title_elem = elem.locator('h3')
                        link_elem = elem.locator('a').first
                        if title_elem.count() > 0 and link_elem.count() > 0:
                            title = title_elem.inner_text()
                            link = link_elem.get_attribute('href')
                            search_results.append({'title': title, 'url': link})
                    except:
                        pass
            except:
                pass

            results['sources'].append({
                'source': 'Google Search',
                'query': 'google nest best buy display retail',
                'results_found': len(search_results),
                'top_results': search_results[:5]
            })

            print(f'  ✅ Google搜索: 找到 {len(search_results)} 个结果')

        except Exception as e:
            print(f'  ❌ Google搜索失败: {e}')

        # 4. 抓取Reddit相关讨论
        print('\\n💬 抓取Reddit讨论...')
        try:
            page.goto('https://www.reddit.com/r/Nest/search/?q=display',
                     wait_until='domcontentloaded', timeout=30000)
            time.sleep(3)

            # 提取帖子标题
            posts = []
            try:
                post_elements = page.locator('[data-testid="post-container"]').all()
                for elem in post_elements[:10]:
                    try:
                        title = elem.locator('h3').inner_text()
                        posts.append(title)
                    except:
                        pass
            except:
                pass

            results['sources'].append({
                'source': 'Reddit r/Nest',
                'posts_found': len(posts),
                'sample_posts': posts[:3]
            })

            print(f'  ✅ Reddit: 找到 {len(posts)} 个相关帖子')

        except Exception as e:
            print(f'  ❌ Reddit 抓取失败: {e}')

        browser.close()

    # 保存结果
    output_file = 'nest_display_info.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print(f'\\n✅ 完成！结果已保存到: {output_file}')
    print(f'抓取了 {len(results["sources"])} 个来源')

    return results

if __name__ == '__main__':
    print('=' * 70)
    print('🔍 Google Nest 展陈信息抓取')
    print('=' * 70)
    print()

    results = scrape_google_nest_info()

    print('\\n' + '=' * 70)
    print('📊 抓取总结:')
    for source in results['sources']:
        status = source.get('status', 'success')
        print(f'  {source["source"]}: {status}')
    print('=' * 70)
