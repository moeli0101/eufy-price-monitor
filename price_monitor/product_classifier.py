#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
产品分类器 - 统一的分类逻辑
确保所有产品都被正确分类
"""

def classify_product(product_name, brand=''):
    """
    根据产品名称判断品类

    Args:
        product_name: 产品名称
        brand: 品牌名称（可选）

    Returns:
        str: 'Video Doorbell', 'Smart Lock', 'Security Camera', 或 'Baby'
    """
    name_lower = product_name.lower()

    # 1. 母婴产品判断（最高优先级）
    baby_keywords = ['baby', 'breast pump', 'nursing', 'infant', 'newborn', 'sock', 'monitor baby']
    if any(kw in name_lower for kw in baby_keywords):
        return 'Baby'

    # 2. 门铃判断
    doorbell_keywords = ['doorbell', 'door bell', 'video door']
    if any(kw in name_lower for kw in doorbell_keywords):
        return 'Video Doorbell'

    # 3. 门锁判断
    lock_keywords = ['lock', 'deadbolt', 'door lock', 'smart lock']
    lock_exclusions = ['unlock', 'lock kit']  # 排除词

    is_lock = any(kw in name_lower for kw in lock_keywords)
    has_exclusion = any(ex in name_lower for ex in lock_exclusions)

    if is_lock and not has_exclusion:
        return 'Smart Lock'

    # 4. 默认为安防相机
    return 'Security Camera'


def is_valid_product(product_name):
    """
    判断是否是有效的产品（不是配件）

    Args:
        product_name: 产品名称

    Returns:
        bool: True if valid product, False if accessory
    """
    name_lower = product_name.lower()

    # 配件关键词
    accessory_keywords = [
        'cable', 'mount', 'bracket', 'solar panel', 'adapter',
        'charging', 'charger', 'battery', 'cover', 'skin',
        'silicone cover', 'wall mount', 'ceiling mount',
        'stand alone', 'replacement'
    ]

    # 但如果包含以下关键词，即使有配件词也算有效产品
    valid_keywords = [
        'doorbell with chime',  # 门铃+响铃器套装
        'camera with',  # 相机套装
        'kit',  # 套装
    ]

    # 检查是否是套装产品
    is_kit = any(kw in name_lower for kw in valid_keywords)

    # 检查是否是配件
    is_accessory = any(kw in name_lower for kw in accessory_keywords)

    # 套装产品即使包含配件词也算有效
    if is_kit:
        return True

    # 纯配件无效
    if is_accessory:
        return False

    return True


def validate_product_data(product):
    """
    验证产品数据完整性

    Args:
        product: 产品字典

    Returns:
        tuple: (is_valid, error_message)
    """
    required_fields = ['name', 'brand', 'category', 'url', 'channel']

    for field in required_fields:
        if field not in product or not product[field]:
            return False, f"Missing required field: {field}"

    # 验证category值
    valid_categories = ['Security Camera', 'Video Doorbell', 'Smart Lock', 'Baby']
    if product['category'] not in valid_categories:
        return False, f"Invalid category: {product['category']}"

    # 验证URL格式
    if not product['url'].startswith('https://www.jbhifi.com.au/products/'):
        return False, f"Invalid URL format: {product['url']}"

    return True, None


if __name__ == '__main__':
    # 测试分类器
    test_cases = [
        ("eufy Security E340 Dual Camera Video Doorbell", "eufy", "Video Doorbell"),
        ("Swann Evo Wireless Video Doorbell (Black)", "Swann", "Video Doorbell"),
        ("TP-Link Tapo 2K Smart Video Doorbell", "TP-Link", "Video Doorbell"),
        ("eufy C210 2K Indoor Security Camera", "eufy", "Security Camera"),
        ("Swann MaxTrak 4K AI Auto Tracking Camera", "Swann", "Security Camera"),
        ("Yale ByYou Pro Smart Mortice Lock", "Yale", "Smart Lock"),
        ("eufy Familock S3 Max Video Smart Lock", "eufy", "Smart Lock"),
        ("Aqara Smart Door Lock D100", "Aqara", "Smart Lock"),
    ]

    print("🧪 测试产品分类器...\n")

    all_passed = True
    for name, brand, expected in test_cases:
        result = classify_product(name, brand)
        status = "✅" if result == expected else "❌"
        if result != expected:
            all_passed = False
        print(f"{status} {name}")
        print(f"   期望: {expected}, 实际: {result}\n")

    if all_passed:
        print("🎉 所有测试通过！")
    else:
        print("⚠️  部分测试失败")
