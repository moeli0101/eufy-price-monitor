#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据验证脚本
检查price_results_latest.json的数据质量
"""

import json
import sys
from product_classifier import classify_product

def validate_price_data(data_file='price_results_latest.json'):
    """验证价格数据的完整性和正确性"""

    print('=' * 70)
    print('🔍 数据验证报告')
    print('=' * 70)

    try:
        with open(data_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        print(f'❌ 无法读取数据文件: {e}')
        return False

    total = len(data)
    print(f'\n📊 总产品数: {total}')

    # 1. 验证必填字段
    print(f'\n1️⃣  验证必填字段...')
    required_fields = ['name', 'brand', 'category', 'url', 'channel', 'status']
    missing_fields = []

    for i, product in enumerate(data):
        for field in required_fields:
            if field not in product or not product[field]:
                missing_fields.append((i, product.get('name', 'Unknown'), field))

    if missing_fields:
        print(f'   ❌ 发现 {len(missing_fields)} 个字段缺失问题')
        for idx, name, field in missing_fields[:5]:
            print(f'      • [{idx}] {name[:40]}... 缺少: {field}')
        if len(missing_fields) > 5:
            print(f'      ... 还有 {len(missing_fields) - 5} 个问题')
    else:
        print(f'   ✅ 所有产品字段完整')

    # 2. 验证分类正确性
    print(f'\n2️⃣  验证分类正确性...')
    wrong_categories = []

    for i, product in enumerate(data):
        expected_category = classify_product(product['name'], product.get('brand', ''))
        actual_category = product.get('category', '')

        if expected_category != actual_category:
            wrong_categories.append((i, product['name'], actual_category, expected_category))

    if wrong_categories:
        print(f'   ⚠️  发现 {len(wrong_categories)} 个分类错误')
        for idx, name, actual, expected in wrong_categories[:5]:
            print(f'      • [{idx}] {name[:40]}...')
            print(f'        实际: {actual}, 应该: {expected}')
        if len(wrong_categories) > 5:
            print(f'      ... 还有 {len(wrong_categories) - 5} 个问题')
    else:
        print(f'   ✅ 所有产品分类正确')

    # 3. 验证价格数据
    print(f'\n3️⃣  验证价格数据...')
    success_count = sum(1 for p in data if p.get('status') == 'success' and p.get('price'))
    failed_count = total - success_count

    print(f'   • 成功抓取: {success_count} ({success_count*100//total}%)')
    print(f'   • 失败: {failed_count}')

    if failed_count > 0:
        print(f'\n   失败产品:')
        failed_products = [p for p in data if p.get('status') != 'success' or not p.get('price')]
        for p in failed_products[:10]:
            print(f'      • {p["name"][:50]}...')
            print(f'        URL: {p["url"][:60]}...')
        if len(failed_products) > 10:
            print(f'      ... 还有 {len(failed_products) - 10} 个')

    # 4. 品类统计
    print(f'\n4️⃣  品类统计...')
    category_stats = {}
    brand_stats = {}

    for p in data:
        cat = p.get('category', 'Unknown')
        brand = p.get('brand', 'Unknown')

        category_stats[cat] = category_stats.get(cat, 0) + 1
        brand_stats[brand] = brand_stats.get(brand, 0) + 1

    print(f'   品类分布:')
    for cat, count in sorted(category_stats.items()):
        print(f'      • {cat}: {count} 款')

    print(f'\n   品牌分布:')
    for brand, count in sorted(brand_stats.items(), key=lambda x: x[1], reverse=True):
        print(f'      • {brand}: {count} 款')

    # 5. 促销统计
    print(f'\n5️⃣  促销统计...')
    promo_count = sum(1 for p in data if p.get('was_price'))
    if promo_count > 0:
        print(f'   • 促销产品: {promo_count} 款')
        top_discounts = sorted(
            [(p['name'], p.get('discount_percent', 0)) for p in data if p.get('discount_percent')],
            key=lambda x: x[1],
            reverse=True
        )[:5]

        print(f'   • Top 5 折扣:')
        for name, discount in top_discounts:
            print(f'      • {name[:45]}... ({discount}% OFF)')
    else:
        print(f'   • 无促销产品')

    # 6. 总结
    print(f'\n' + '=' * 70)

    all_good = (
        len(missing_fields) == 0 and
        len(wrong_categories) == 0 and
        success_count / total >= 0.8
    )

    if all_good:
        print('✅ 数据质量良好！')
        print('=' * 70)
        return True
    else:
        print('⚠️  数据存在问题，需要修复')
        print('=' * 70)
        return False


if __name__ == '__main__':
    success = validate_price_data()
    sys.exit(0 if success else 1)
