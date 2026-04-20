#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
每日价格自动刷新脚本 - 固定产品列表版
从 product_list_fixed.json 读取固定产品列表，逐一抓取价格
不再依赖动态搜索，成功率更稳定
"""

from playwright.sync_api import sync_playwright
import json
import time
import random
from datetime import datetime
from pathlib import Path
from product_classifier import classify_product, is_valid_product, validate_product_data
from price_history_manager import PriceHistoryManager
from promotion_detector import PromotionDetector
from promotion_calendar_generator import PromotionCalendarGenerator

# ─── User-Agent 池（轮换使用，降低被限速概率）─────────────────────────────────
USER_AGENTS = [
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.3 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:124.0) Gecko/20100101 Firefox/124.0",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
]


def load_product_list():
    """加载固定产品列表"""
    list_file = Path("product_list_fixed.json")
    if list_file.exists():
        with open(list_file, "r", encoding="utf-8") as f:
            products = json.load(f)
        print(f"📋 加载固定产品列表: {len(products)} 个产品")
        return products
    else:
        print("⚠️  product_list_fixed.json 不存在，将从 price_history.json 重新生成...")
        return generate_product_list_from_history()


def generate_product_list_from_history():
    """从历史数据生成产品列表（备用方案）"""
    history_file = Path("price_history.json")
    if not history_file.exists():
        print("❌ price_history.json 也不存在，无法生成产品列表")
        return []

    with open(history_file, "r", encoding="utf-8") as f:
        history = json.load(f)

    products = []
    for key, data in history.items():
        products.append(
            {
                "name": data["product_name"],
                "brand": data["brand"],
                "category": data["category"],
                "url": data["url"],
                "channel": data.get("channel", "JB Hi-Fi"),
            }
        )

    print(f"✅ 从历史数据生成产品列表: {len(products)} 个")

    # 保存以便下次直接使用
    with open("product_list_fixed.json", "w", encoding="utf-8") as f:
        json.dump(products, f, ensure_ascii=False, indent=2)

    return products


def extract_price(page):
    """
    提取价格 - 多选择器 fallback，同时获取原价和促销价
    选择器按优先级排列，任意一个成功即返回
    """
    try:
        time.sleep(1.5)

        current_price = None
        was_price = None

        # 1. 主选择器：ticket-price（JB Hi-Fi 现价）
        try:
            ticket = page.locator('[data-testid="ticket-price"]').first
            if ticket.count() > 0:
                text = ticket.inner_text().strip().replace(",", "").replace("$", "")
                if text:
                    current_price = float(text)
        except Exception:
            pass

        # 2. Fallback：price-tag 类
        if current_price is None:
            try:
                for sel in [
                    ".price-tag__price",
                    '[class*="price-tag"]',
                    '[class*="PriceTag"]',
                ]:
                    elems = page.locator(sel)
                    if elems.count() > 0:
                        text = (
                            elems.first.inner_text()
                            .strip()
                            .replace(",", "")
                            .replace("$", "")
                        )
                        if text:
                            current_price = float(text)
                            break
            except Exception:
                pass

        # 3. Fallback：JSON-LD 结构化数据（最可靠）
        if current_price is None:
            try:
                import re

                content = page.content()
                # JB Hi-Fi 页面里有 JSON-LD 包含价格
                ld_matches = re.findall(r'"price"\s*:\s*"?([\d.]+)"?', content)
                if ld_matches:
                    for price_str in ld_matches:
                        val = float(price_str)
                        if 1 < val < 50000:
                            current_price = val
                            break
            except Exception:
                pass

        # 4. 抓取原价（划线价）
        try:
            strike = page.locator(
                '[data-testid="floating-header-strikethrough-price"]'
            ).first
            if strike.count() > 0:
                text = strike.inner_text().strip().replace(",", "").replace("$", "")
                if text:
                    was_price = float(text)
        except Exception:
            pass

        # 验证价格合理性（JB Hi-Fi 产品价格范围）
        if current_price and 1 < current_price < 50000:
            result = {"price": current_price}
            if was_price and was_price > current_price:
                result["was_price"] = was_price
                result["discount_percent"] = round(
                    (was_price - current_price) / was_price * 100
                )
            return result

        return None

    except Exception:
        return None


def scrape_single_product(browser, product, max_retries=3):
    """
    抓取单个产品价格，带重试机制
    每次重试使用不同 User-Agent
    """
    page = None
    for attempt in range(max_retries):
        try:
            ua = random.choice(USER_AGENTS)
            page = browser.new_page(
                user_agent=ua, viewport={"width": 1920, "height": 1080}
            )

            page.goto(product["url"], wait_until="domcontentloaded", timeout=30000)
            price_data = extract_price(page)
            page.close()
            page = None

            if price_data:
                return price_data, True

            # 无价格数据，等待后重试
            if attempt < max_retries - 1:
                time.sleep(random.uniform(2, 4))

        except Exception as e:
            if page:
                try:
                    page.close()
                except Exception:
                    pass
                page = None
            if attempt < max_retries - 1:
                time.sleep(random.uniform(2, 5))

    return None, False


def scrape_prices(products):
    """抓取所有产品价格（固定列表版）"""
    total = len(products)
    print(f"\n💰 抓取价格 ({total} 款)...")

    results = []

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-dev-shm-usage",
                "--disable-gpu",
            ],
        )

        success_count = 0
        fail_count = 0

        for i, product in enumerate(products, 1):
            # 进度日志（每10个打印一次，方便调试）
            if i % 10 == 0 or i == 1:
                rate = round(success_count / (i - 1) * 100) if i > 1 else 0
                print(
                    f"  进度: {i}/{total} | 成功:{success_count} 失败:{fail_count} 成功率:{rate}%"
                )

            price_data, success = scrape_single_product(browser, product, max_retries=3)

            result = {
                "name": product["name"],
                "brand": product["brand"],
                "category": product.get("category", "Security Camera"),
                "channel": product.get("channel", "JB Hi-Fi"),
                "url": product["url"],
                "currency": "AUD",
                "scraped_at": datetime.now().isoformat(),
            }

            if success and price_data:
                result["price"] = price_data["price"]
                if "was_price" in price_data:
                    result["was_price"] = price_data["was_price"]
                if "discount_percent" in price_data:
                    result["discount_percent"] = price_data["discount_percent"]
                result["status"] = "success"
                success_count += 1
            else:
                result["price"] = None
                result["status"] = "failed"
                fail_count += 1

            results.append(result)

            # 随机间隔：1-3秒，防止被限速
            time.sleep(random.uniform(1.0, 3.0))

        browser.close()

    return results


def main():
    print("=" * 70)
    print("🤖 每日价格自动刷新（固定产品列表版）")
    print(f"⏰ 运行时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)

    # 1. 加载固定产品列表
    products = load_product_list()

    if not products:
        print("❌ 无法加载产品列表，退出")
        return

    # 按品类统计
    from collections import Counter

    category_stats = Counter(p["category"] for p in products)
    brand_stats = Counter(p["brand"] for p in products)

    print(f"\n📊 产品列表统计:")
    print(f"  总计: {len(products)} 款")
    print(f"\n📂 品类分布:")
    for cat, count in sorted(category_stats.items()):
        print(f"  {cat}: {count} 款")
    print(f"\n🏷️  主要品牌:")
    for brand, count in sorted(brand_stats.items(), key=lambda x: -x[1])[:8]:
        print(f"  {brand}: {count} 款")

    # 2. 抓取价格
    results = scrape_prices(products)

    # 3. 保存最新价格数据
    with open("price_results_latest.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    # 4. 更新历史数据 & 检测促销
    print(f"\n📊 更新历史数据和检测促销...")
    history_manager = PriceHistoryManager()
    promotion_detector = PromotionDetector()

    promotion_count = 0
    for result in results:
        if result["status"] != "success" or not result.get("price"):
            continue

        product_id = history_manager.update_price(result)

        current_price = result["price"]
        original_price = result.get("was_price", current_price)

        promotion_detector.update_promotions(
            product_id=product_id,
            product_name=result["name"],
            brand=result["brand"],
            category=result["category"],
            current_price=current_price,
            original_price=original_price,
            url=result.get("url", ""),
        )

        if result.get("was_price") and result["was_price"] > current_price:
            promotion_count += 1

    history_manager.save_history()
    promotion_detector.save_promotions()

    print(f"  历史记录: {len(history_manager.history)} 个产品")
    print(f"  促销中: {promotion_count} 款")

    # 5. 统计结果
    success_count = sum(1 for r in results if r["status"] == "success")
    fail_count = len(results) - success_count
    success_rate = round(success_count / len(results) * 100) if results else 0

    print(f"\n{'=' * 70}")
    print(f"✅ 完成！")
    print(f"  成功: {success_count}/{len(results)} ({success_rate}%)")
    print(f"  失败: {fail_count} 款")
    print(f"  数据已保存到: price_results_latest.json")
    print(f"{'=' * 70}")

    # 6. 记录运行日志
    cameras = sum(1 for r in results if r.get("category") == "Security Camera")
    doorbells = sum(1 for r in results if r.get("category") == "Video Doorbell")
    locks = sum(1 for r in results if r.get("category") == "Smart Lock")
    baby = sum(1 for r in results if r.get("category") == "Baby")

    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "total_products": len(results),
        "success_count": success_count,
        "fail_count": fail_count,
        "success_rate": success_rate,
        "cameras": cameras,
        "doorbells": doorbells,
        "locks": locks,
        "baby": baby,
        "eufy_count": sum(1 for r in results if r.get("brand") == "eufy"),
    }

    try:
        with open("price_refresh_log.json", "r", encoding="utf-8") as f:
            logs = json.load(f)
    except Exception:
        logs = []

    logs.append(log_entry)
    if len(logs) > 30:
        logs = logs[-30:]

    with open("price_refresh_log.json", "w", encoding="utf-8") as f:
        json.dump(logs, f, ensure_ascii=False, indent=2)

    # 7. 生成促销日历
    print(f"\n📅 生成促销日历...")
    calendar_generator = PromotionCalendarGenerator()
    now = datetime.now()
    calendar = calendar_generator.generate_monthly_calendar(now.year, now.month)
    calendar_generator.save_calendar_json(calendar)
    print(f"  生成了 {len(calendar)} 个产品的日历")


if __name__ == "__main__":
    main()
