#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
健康检查脚本 - 验证数据完整性
"""

import json
import sys
from datetime import datetime, timedelta
from pathlib import Path

def check_file_exists(filepath):
    """检查文件是否存在"""
    if not Path(filepath).exists():
        return False, f"文件不存在: {filepath}"

    size = Path(filepath).stat().st_size
    if size < 100:
        return False, f"文件太小 ({size} bytes): {filepath}"

    return True, f"✅ {filepath}: {size:,} bytes"

def check_json_valid(filepath):
    """检查JSON格式是否正确"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return True, f"✅ JSON格式正确: {filepath}"
    except json.JSONDecodeError as e:
        return False, f"JSON格式错误: {filepath} - {e}"

def check_data_freshness(filepath, max_age_days=2):
    """检查数据是否新鲜"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # 获取最新记录日期
        latest_date = None
        if isinstance(data, dict):
            for product_id, product_data in data.items():
                if 'price_history' in product_data and product_data['price_history']:
                    record_date = product_data['price_history'][-1]['date']
                    if not latest_date or record_date > latest_date:
                        latest_date = record_date

        if not latest_date:
            return False, "找不到最新日期"

        latest_datetime = datetime.strptime(latest_date, '%Y-%m-%d')
        age_days = (datetime.now() - latest_datetime).days

        if age_days > max_age_days:
            return False, f"数据过期 {age_days} 天（最新: {latest_date}）"

        return True, f"✅ 数据新鲜（最新: {latest_date}，{age_days}天前）"

    except Exception as e:
        return False, f"检查失败: {e}"

def check_product_count(filepath, min_products=50):
    """检查产品数量"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)

        count = len(data) if isinstance(data, dict) else len(data)

        if count < min_products:
            return False, f"产品数量太少: {count} < {min_products}"

        return True, f"✅ 产品数量: {count}"

    except Exception as e:
        return False, f"检查失败: {e}"

def main():
    print("🔍 价格监控系统健康检查")
    print("=" * 60)

    checks = []

    # 检查核心文件
    files_to_check = [
        'price_history.json',
        'promotions.json',
        'price_results_latest.json',
        'docs/price_history.json',
        'docs/promotions.json',
        'docs/price_results_latest.json',
        'docs/price_tracker.html'
    ]

    for filepath in files_to_check:
        success, message = check_file_exists(filepath)
        checks.append((success, message))
        print(message)

    print("\n" + "=" * 60)
    print("📋 JSON格式验证")
    print("=" * 60)

    json_files = [
        'price_history.json',
        'promotions.json',
        'price_results_latest.json'
    ]

    for filepath in json_files:
        if Path(filepath).exists():
            success, message = check_json_valid(filepath)
            checks.append((success, message))
            print(message)

    print("\n" + "=" * 60)
    print("⏰ 数据新鲜度检查")
    print("=" * 60)

    success, message = check_data_freshness('price_history.json')
    checks.append((success, message))
    print(message)

    print("\n" + "=" * 60)
    print("📊 产品数量检查")
    print("=" * 60)

    success, message = check_product_count('price_history.json', min_products=50)
    checks.append((success, message))
    print(message)

    print("\n" + "=" * 60)
    print("📈 数据统计")
    print("=" * 60)

    try:
        with open('price_history.json', 'r', encoding='utf-8') as f:
            history = json.load(f)

        total_products = len(history)
        total_records = sum(len(p['price_history']) for p in history.values())
        max_days = max(len(p['price_history']) for p in history.values())

        brands = {}
        categories = {}
        on_sale = 0

        for product_data in history.values():
            brand = product_data['brand']
            cat = product_data['category']
            brands[brand] = brands.get(brand, 0) + 1
            categories[cat] = categories.get(cat, 0) + 1

            if product_data['price_history'][-1].get('is_on_sale'):
                on_sale += 1

        print(f"总产品数: {total_products}")
        print(f"总价格记录: {total_records:,}")
        print(f"最长历史: {max_days} 天")
        print(f"当前促销: {on_sale} 个")
        print(f"\n品牌分布:")
        for brand, count in sorted(brands.items(), key=lambda x: -x[1]):
            print(f"  {brand}: {count}")
        print(f"\n品类分布:")
        for cat, count in sorted(categories.items(), key=lambda x: -x[1]):
            print(f"  {cat}: {count}")

    except Exception as e:
        print(f"统计失败: {e}")

    print("\n" + "=" * 60)
    print("🎯 检查结果")
    print("=" * 60)

    failed = sum(1 for success, _ in checks if not success)
    passed = sum(1 for success, _ in checks if success)

    print(f"通过: {passed}/{len(checks)}")
    print(f"失败: {failed}/{len(checks)}")

    if failed > 0:
        print("\n❌ 健康检查失败")
        sys.exit(1)
    else:
        print("\n✅ 系统健康")
        sys.exit(0)

if __name__ == '__main__':
    main()
