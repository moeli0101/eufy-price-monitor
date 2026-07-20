#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
每日价格自动刷新脚本 - HTTP requests 版
不使用 Playwright，直接 HTTP 请求抓取页面，绕过 Cloudflare 检测
"""

import json
import time
import random
import re
from datetime import datetime
from pathlib import Path
import requests
from product_classifier import classify_product, is_valid_product, validate_product_data
from price_history_manager import PriceHistoryManager
from promotion_detector import PromotionDetector
from promotion_calendar_generator import PromotionCalendarGenerator

USER_AGENTS = [
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.3 Safari/605.1.15',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:124.0) Gecko/20100101 Firefox/124.0',
]

HEADERS = {
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'en-AU,en;q=0.9',
    'Accept-Encoding': 'gzip, deflate, br',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
}


def load_product_list():
    list_file = Path('product_list_fixed.json')
    if list_file.exists():
        with open(list_file, 'r', encoding='utf-8') as f:
            products = json.load(f)
        print(f'📋 加载固定产品列表: {len(products)} 个产品')
        return products
    else:
        print('⚠️  product_list_fixed.json 不存在')
        return []


def extract_price_from_html(content):
    current_price = None
    was_price = None

    is_clearance = 'pdp-banner-tag' in content and 'CLEARANCE' in content[content.index('pdp-banner-tag')-200:content.index('pdp-banner-tag')+200] if 'pdp-banner-tag' in content else False

    # variant-button
    m = re.search(r'data-test-id="variant-button"[^>]*class="[^"]*current[^"]*"[^>]*data-price="([\d.]+)"[^>]*data-core-price="([\d.]+)"', content)
    if not m:
        m = re.search(r'data-price="([\d.]+)"[^>]*data-core-price="([\d.]+)"[^>]*data-test-id="variant-button"[^>]*class="[^"]*current', content)
    if m:
        p = float(m.group(1))
        c = float(m.group(2))
        if 1 < p < 50000:
            current_price = p
        if current_price and 1 < c < 50000 and c > current_price:
            was_price = c

    # Price JSON block
    if current_price is None:
        m = re.search(r'"Price":\{([^}]+)\}', content)
        if m:
            try:
                price_obj = json.loads('{' + m.group(1) + '}')
                display = price_obj.get('DisplayPriceInc')
                display_was = price_obj.get('DisplayWasPrice', False)
                save = price_obj.get('SaveAmount', 0)
                core = price_obj.get('CoreTicketPrice')
                if display and 1 < display < 50000:
                    current_price = display
                    if core and core > display:
                        if is_clearance:
                            was_price = core if (save < 0 and display_was) else None
                        else:
                            was_price = core
            except Exception:
                pass

    # Fallback: ticket-price in HTML
    if current_price is None:
        m = re.search(r'data-testid="ticket-price"[^>]*>([\d,]+)<', content)
        if m:
            p = float(m.group(1).replace(',', ''))
            if 1 < p < 50000:
                current_price = p

    # Fallback: JSON-LD
    if current_price is None:
        ld_matches = re.findall(r'"price"\s*:\s*"?([\d.]+)"?', content)
        for price_str in ld_matches:
            val = float(price_str)
            if 1 < val < 50000:
                current_price = val
                break

    if current_price is None:
        return None

    result = {'price': current_price}
    if was_price:
        result['was_price'] = was_price
        result['discount_percent'] = round((was_price - current_price) / was_price * 100)
    return result


def scrape_single_product(session, product, max_retries=3):
    for attempt in range(max_retries):
        try:
            headers = dict(HEADERS)
            headers['User-Agent'] = random.choice(USER_AGENTS)

            resp = session.get(product['url'], headers=headers, timeout=25)

            if resp.status_code in (429, 503):
                wait = random.uniform(5, 10) if resp.status_code == 429 else random.uniform(3, 6)
                if attempt < max_retries - 1:
                    time.sleep(wait)
                    continue
                return None, False

            if resp.status_code != 200 or len(resp.text) < 5000:
                if attempt < max_retries - 1:
                    time.sleep(random.uniform(2, 4))
                    continue
                return None, False

            result = extract_price_from_html(resp.text)
            if result:
                return result, True

            if attempt < max_retries - 1:
                time.sleep(random.uniform(2, 4))
        except Exception:
            if attempt < max_retries - 1:
                time.sleep(random.uniform(2, 5))

    return None, False


def scrape_prices(products):
    total = len(products)
    print(f'\n💰 抓取价格 ({total} 款)...')

    results = []
    session = requests.Session()

    success_count = 0
    fail_count = 0

    for i, product in enumerate(products, 1):
        if i % 10 == 0 or i == 1:
            rate = round(success_count / (i - 1) * 100) if i > 1 else 0
            print(f'  进度: {i}/{total} | 成功:{success_count} 失败:{fail_count} 成功率:{rate}%', flush=True)

        price_data, success = scrape_single_product(session, product, max_retries=2)

        result = {
            'name': product['name'],
            'brand': product['brand'],
            'category': product.get('category', 'Security Camera'),
            'channel': product.get('channel', 'JB Hi-Fi'),
            'url': product['url'],
            'currency': 'AUD',
            'scraped_at': datetime.now().isoformat(),
        }

        if success and price_data:
            result['price'] = price_data['price']
            if 'was_price' in price_data:
                result['was_price'] = price_data['was_price']
            if 'discount_percent' in price_data:
                result['discount_percent'] = price_data['discount_percent']
            result['status'] = 'success'
            success_count += 1
        else:
            result['price'] = None
            result['status'] = 'failed'
            fail_count += 1

        results.append(result)
        time.sleep(random.uniform(0.5, 1.5))

    session.close()
    return results


def main():
    print('=' * 70)
    print('🤖 每日价格自动刷新（HTTP requests 版）')
    print(f'⏰ 运行时间: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
    print('=' * 70)

    products = load_product_list()
    if not products:
        print('❌ 无法加载产品列表，退出')
        return

    from collections import Counter
    category_stats = Counter(p['category'] for p in products)
    brand_stats = Counter(p['brand'] for p in products)

    print(f'\n📊 产品列表统计:')
    print(f'  总计: {len(products)} 款')
    print(f'\n📂 品类分布:')
    for cat, count in sorted(category_stats.items()):
        print(f'  {cat}: {count} 款')
    print(f'\n🏷️  主要品牌:')
    for brand, count in sorted(brand_stats.items(), key=lambda x: -x[1])[:8]:
        print(f'  {brand}: {count} 款')

    results = scrape_prices(products)

    with open('price_results_latest.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print(f'\n📊 更新历史数据和检测促销...')
    history_manager = PriceHistoryManager()
    promotion_detector = PromotionDetector()

    promotion_count = 0
    for result in results:
        if result['status'] != 'success' or not result.get('price'):
            continue
        product_id = history_manager.update_price(result)
        current_price = result['price']
        original_price = result.get('was_price', current_price)
        promotion_detector.update_promotions(
            product_id=product_id,
            product_name=result['name'],
            brand=result['brand'],
            category=result['category'],
            current_price=current_price,
            original_price=original_price,
            url=result.get('url', '')
        )
        if result.get('was_price') and result['was_price'] > current_price:
            promotion_count += 1

    history_manager.save_history()
    promotion_detector.save_promotions()

    print(f'  历史记录: {len(history_manager.history)} 个产品')
    print(f'  促销中: {promotion_count} 款')

    success_count = sum(1 for r in results if r['status'] == 'success')
    fail_count = len(results) - success_count
    success_rate = round(success_count / len(results) * 100) if results else 0

    print(f'\n{"=" * 70}')
    print(f'✅ 完成！')
    print(f'  成功: {success_count}/{len(results)} ({success_rate}%)')
    print(f'  失败: {fail_count} 款')
    print(f'  数据已保存到: price_results_latest.json')
    print(f'{"=" * 70}')

    cameras = sum(1 for r in results if r.get('category') == 'Security Camera')
    doorbells = sum(1 for r in results if r.get('category') == 'Video Doorbell')
    locks = sum(1 for r in results if r.get('category') == 'Smart Lock')
    baby = sum(1 for r in results if r.get('category') == 'Baby')

    log_entry = {
        'timestamp': datetime.now().isoformat(),
        'total_products': len(results),
        'success_count': success_count,
        'fail_count': fail_count,
        'success_rate': success_rate,
        'cameras': cameras,
        'doorbells': doorbells,
        'locks': locks,
        'baby': baby,
        'eufy_count': sum(1 for r in results if r.get('brand') == 'eufy'),
    }

    try:
        with open('price_refresh_log.json', 'r', encoding='utf-8') as f:
            logs = json.load(f)
    except Exception:
        logs = []

    logs.append(log_entry)
    if len(logs) > 30:
        logs = logs[-30:]

    with open('price_refresh_log.json', 'w', encoding='utf-8') as f:
        json.dump(logs, f, ensure_ascii=False, indent=2)

    print(f'\n📅 生成促销日历...')
    calendar_generator = PromotionCalendarGenerator()
    now = datetime.now()
    calendar = calendar_generator.generate_monthly_calendar(now.year, now.month)
    calendar_generator.save_calendar_json(calendar)
    print(f'  生成了 {len(calendar)} 个产品的日历')


if __name__ == '__main__':
    main()
