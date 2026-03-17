#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
每日价格自动刷新脚本
自动从JB Hi-Fi抓取所有eufy和竞品camera的最新价格
"""

from playwright.sync_api import sync_playwright
import json
import time
import re
from datetime import datetime

def search_all_eufy_cameras():
    """搜索所有eufy camera产品"""
    print('🔍 搜索eufy产品...')

    all_products = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        # 搜索eufy camera
        search_url = 'https://www.jbhifi.com.au/search?query=eufy+camera&page=1'
        page.goto(search_url, wait_until='domcontentloaded', timeout=20000)
        time.sleep(3)

        content = page.content()
        product_urls = re.findall(r'href="(/products/[^"]+)"', content)
        unique_urls = list(set(product_urls))

        print(f'  第1页: {len(unique_urls)} 个链接')

        # 第2页
        page.goto('https://www.jbhifi.com.au/search?query=eufy+camera&page=2', timeout=20000)
        time.sleep(3)
        content = page.content()
        product_urls_p2 = re.findall(r'href="(/products/[^"]+)"', content)
        unique_urls.extend([url for url in set(product_urls_p2) if url not in unique_urls])

        print(f'  第2页: 新增 {len(set(product_urls_p2)) - len(unique_urls) + len(set(product_urls_p2))} 个链接')

        # 访问每个产品页
        for url in unique_urls:
            full_url = f'https://www.jbhifi.com.au{url}'

            # 避免重复
            if any(p['url'] == full_url for p in all_products):
                continue

            try:
                detail_page = browser.new_page()
                detail_page.goto(full_url, wait_until='domcontentloaded', timeout=15000)
                time.sleep(1)

                try:
                    title = detail_page.locator('h1').first.inner_text()
                    title_lower = title.lower()

                    # 是eufy camera
                    if 'eufy' in title_lower and any(kw in title_lower for kw in ['camera', 'cam', 'eufycam', 'security', 'video', 'doorbell', 'baby monitor']):
                        # 排除配件
                        if not any(kw in title_lower for kw in ['cable', 'mount', 'bracket', 'solar panel', 'adapter']):
                            # 判断是否是门铃
                            category = 'Video Doorbell' if 'doorbell' in title_lower else 'Security Camera'
                            all_products.append({
                                'name': title,
                                'brand': 'eufy',
                                'category': category,
                                'url': full_url,
                                'channel': 'JB Hi-Fi'
                            })
                except:
                    pass

                detail_page.close()
                time.sleep(0.3)

            except:
                pass

        browser.close()

    return all_products

def search_doorbell_lock():
    """搜索门铃和门锁"""
    print('\n🔍 搜索门铃和门锁...')

    products = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)

        search_terms = ['smart doorbell', 'smart lock']

        for term in search_terms:
            print(f'  搜索: {term}')
            page = browser.new_page()

            try:
                search_url = f'https://www.jbhifi.com.au/search?query={term.replace(" ", "+")}'
                page.goto(search_url, timeout=20000)
                time.sleep(3)

                content = page.content()
                product_urls = re.findall(r'href="(/products/[^"]+)"', content)
                unique_urls = list(set(product_urls))

                for url in unique_urls[:15]:
                    full_url = f'https://www.jbhifi.com.au{url}'

                    if any(p['url'] == full_url for p in products):
                        continue

                    try:
                        detail_page = browser.new_page()
                        detail_page.goto(full_url, timeout=12000)
                        time.sleep(1)

                        try:
                            title = detail_page.locator('h1').first.inner_text()
                            title_lower = title.lower()

                            is_doorbell = 'doorbell' in title_lower
                            is_lock = 'lock' in title_lower and 'unlock' not in title_lower

                            if (is_doorbell or is_lock) and not any(kw in title_lower for kw in ['cable', 'mount', 'bracket', 'chime', 'adapter', 'battery']):
                                brand = 'Other'
                                if 'eufy' in title_lower:
                                    brand = 'eufy'
                                elif 'ring' in title_lower:
                                    brand = 'Ring'
                                elif 'arlo' in title_lower:
                                    brand = 'Arlo'
                                elif 'yale' in title_lower:
                                    brand = 'Yale'
                                elif 'tp-link' in title_lower or 'tapo' in title_lower:
                                    brand = 'TP-Link'

                                products.append({
                                    'name': title,
                                    'brand': brand,
                                    'category': 'Video Doorbell' if is_doorbell else 'Smart Lock',
                                    'url': full_url,
                                    'channel': 'JB Hi-Fi'
                                })
                        except:
                            pass

                        detail_page.close()
                    except:
                        pass
            except:
                pass

            page.close()

        browser.close()

    return products

def search_competitor_cameras():
    """搜索竞品camera"""
    print('\n🔍 搜索竞品camera...')

    competitors = []
    brands = [
        ('Arlo', 'arlo security camera'),
        ('Ring', 'ring security camera'),
        ('Google Nest', 'google nest cam'),
        ('TP-Link', 'tp-link tapo camera'),
    ]

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)

        for brand_name, search_term in brands:
            print(f'  搜索 {brand_name}...')

            page = browser.new_page()
            search_url = f'https://www.jbhifi.com.au/search?query={search_term.replace(" ", "+")}'

            try:
                page.goto(search_url, wait_until='domcontentloaded', timeout=20000)
                time.sleep(3)

                content = page.content()
                product_urls = re.findall(r'href="(/products/[^"]+)"', content)
                unique_urls = list(set(product_urls))

                for url in unique_urls[:6]:  # 每个品牌取前6个
                    full_url = f'https://www.jbhifi.com.au{url}'

                    try:
                        detail_page = browser.new_page()
                        detail_page.goto(full_url, timeout=15000)
                        time.sleep(1)

                        try:
                            title = detail_page.locator('h1').first.inner_text()
                            title_lower = title.lower()

                            # 确认是目标品牌的camera
                            if brand_name.lower().replace(' ', '') in title_lower.replace(' ', ''):
                                if any(kw in title_lower for kw in ['camera', 'cam', 'doorbell', 'security']):
                                    if not any(kw in title_lower for kw in ['cable', 'mount', 'adapter']):
                                        competitors.append({
                                            'name': title,
                                            'brand': brand_name,
                                            'url': full_url,
                                            'channel': 'JB Hi-Fi'
                                        })
                        except:
                            pass

                        detail_page.close()
                    except:
                        pass
            except:
                pass

            page.close()
            time.sleep(1)

        browser.close()

    return competitors

def extract_price(page):
    """提取价格 - 同时获取原价和促销价"""
    try:
        time.sleep(1.5)

        current_price = None
        was_price = None

        # 1. 抓取实际售价（ticket-price）
        try:
            ticket_price_elem = page.locator('[data-testid="ticket-price"]').first
            if ticket_price_elem.count() > 0:
                text = ticket_price_elem.inner_text()
                current_price = float(text.replace(',', '').strip())
        except:
            pass

        # 2. 抓取原价（floating-header-strikethrough-price，如果有促销的话）
        try:
            was_price_elem = page.locator('[data-testid="floating-header-strikethrough-price"]').first
            if was_price_elem.count() > 0:
                text = was_price_elem.inner_text()
                was_price = float(text.replace(',', '').strip())
        except:
            pass

        # 返回字典，包含当前价和原价
        if current_price and 50 < current_price < 10000:
            result = {'price': current_price}
            if was_price and was_price > current_price:
                result['was_price'] = was_price
                result['discount_percent'] = round((was_price - current_price) / was_price * 100)
            return result

        return None
    except:
        return None

def scrape_prices(products):
    """抓取所有产品价格"""
    print(f'\n💰 抓取价格 ({len(products)} 款)...')

    results = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)

        for i, product in enumerate(products, 1):
            if i % 10 == 0:
                print(f'  进度: {i}/{len(products)}')

            try:
                page = browser.new_page(
                    user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
                )

                page.goto(product['url'], wait_until='domcontentloaded', timeout=15000)
                price_data = extract_price(page)
                page.close()

                result = {
                    'name': product['name'],
                    'brand': product['brand'],
                    'category': product.get('category', 'Security Camera'),
                    'channel': 'JB Hi-Fi',
                    'url': product['url'],
                    'currency': 'AUD',
                    'scraped_at': datetime.now().isoformat(),
                }

                # 处理价格数据
                if price_data:
                    result['price'] = price_data['price']
                    if 'was_price' in price_data:
                        result['was_price'] = price_data['was_price']
                    if 'discount_percent' in price_data:
                        result['discount_percent'] = price_data['discount_percent']
                    result['status'] = 'success'
                else:
                    result['price'] = None
                    result['status'] = 'failed'

                results.append(result)

                time.sleep(1)

            except:
                result = {
                    'name': product['name'],
                    'brand': product['brand'],
                    'category': product.get('category', 'Security Camera'),
                    'channel': 'JB Hi-Fi',
                    'url': product['url'],
                    'price': None,
                    'scraped_at': datetime.now().isoformat(),
                    'status': 'failed'
                }
                results.append(result)

        browser.close()

    return results

def main():
    print('=' * 70)
    print('🤖 每日价格自动刷新')
    print(f'⏰ 运行时间: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
    print('=' * 70)

    # 1. 搜索产品
    eufy_products = search_all_eufy_cameras()
    competitor_products = search_competitor_cameras()
    doorbell_lock_products = search_doorbell_lock()

    # 给camera产品添加category（如果还没有的话）
    for p in eufy_products:
        if 'category' not in p:
            p['category'] = 'Security Camera'
    for p in competitor_products:
        if 'category' not in p:
            p['category'] = 'Security Camera'

    all_products = eufy_products + competitor_products + doorbell_lock_products

    print(f'\n📊 找到产品:')
    print(f'  eufy camera: {len(eufy_products)} 款')
    print(f'  竞品 camera: {len(competitor_products)} 款')
    print(f'  门铃+门锁: {len(doorbell_lock_products)} 款')
    print(f'  总计: {len(all_products)} 款')

    # 2. 抓取价格
    results = scrape_prices(all_products)

    # 3. 保存结果
    with open('/Users/anker/Desktop/feishu_bot/price_results_latest.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    # 4. 统计
    success = sum(1 for r in results if r['status'] == 'success')

    print(f'\n{"=" * 70}')
    print(f'✅ 完成！')
    print(f'  成功: {success}/{len(results)} ({success*100//len(results)}%)')
    print(f'  数据已保存到: price_results_latest.json')
    print(f'{"=" * 70}')

    # 5. 记录日志
    cameras = sum(1 for r in results if (r.get('category', 'Security Camera') == 'Security Camera'))
    doorbells = sum(1 for r in results if r.get('category') == 'Video Doorbell')
    locks = sum(1 for r in results if r.get('category') == 'Smart Lock')

    log_entry = {
        'timestamp': datetime.now().isoformat(),
        'total_products': len(results),
        'success_count': success,
        'cameras': cameras,
        'doorbells': doorbells,
        'locks': locks,
        'eufy_count': len(eufy_products)
    }

    # 追加到日志文件
    try:
        with open('/Users/anker/Desktop/feishu_bot/price_refresh_log.json', 'r', encoding='utf-8') as f:
            logs = json.load(f)
    except:
        logs = []

    logs.append(log_entry)

    # 只保留最近30天的日志
    if len(logs) > 30:
        logs = logs[-30:]

    with open('/Users/anker/Desktop/feishu_bot/price_refresh_log.json', 'w', encoding='utf-8') as f:
        json.dump(logs, f, ensure_ascii=False, indent=2)

if __name__ == '__main__':
    main()
