#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
价格历史管理器
负责记录和管理所有产品的历史价格数据
"""

import json
from datetime import datetime
from pathlib import Path


class PriceHistoryManager:
    def __init__(self, history_file='price_history.json'):
        self.history_file = history_file
        self.history = {}
        self.load_history()

    def load_history(self):
        """加载历史数据"""
        if Path(self.history_file).exists():
            try:
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    self.history = json.load(f)
                print(f'✅ 加载历史数据: {len(self.history)} 个产品')
            except Exception as e:
                print(f'⚠️  加载历史数据失败: {e}')
                self.history = {}
        else:
            print('📝 首次运行，创建新的历史数据文件')
            self.history = {}

    def generate_product_id(self, product_name, brand):
        """生成唯一的产品ID"""
        # 移除特殊字符，转小写，用下划线连接
        clean_name = product_name.lower()
        for char in [' ', '-', '/', '(', ')', ',', '.', '&']:
            clean_name = clean_name.replace(char, '_')
        # 移除连续的下划线
        while '__' in clean_name:
            clean_name = clean_name.replace('__', '_')
        clean_name = clean_name.strip('_')

        # 限制长度
        if len(clean_name) > 60:
            clean_name = clean_name[:60]

        return f"{brand.lower()}_{clean_name}"

    def update_price(self, product_data):
        """更新产品价格"""
        today = datetime.now().strftime("%Y-%m-%d")

        # 生成产品ID
        product_id = self.generate_product_id(
            product_data['name'],
            product_data['brand']
        )

        # 如果是新产品，创建记录
        if product_id not in self.history:
            self.history[product_id] = {
                'product_name': product_data['name'],
                'brand': product_data['brand'],
                'category': product_data.get('category', 'Unknown'),
                'url': product_data.get('url', ''),
                'channel': product_data.get('channel', 'JB Hi-Fi'),
                'price_history': []
            }
            print(f'  新产品: {product_data["name"]}')

        # 检查今天是否已有记录
        history_list = self.history[product_id]['price_history']

        # 如果今天已有记录，更新它；否则添加新记录
        if history_list and history_list[-1]['date'] == today:
            # 更新今天的记录
            history_list[-1] = self._create_price_record(today, product_data)
        else:
            # 添加新的记录
            history_list.append(self._create_price_record(today, product_data))

        return product_id

    def _create_price_record(self, date, product_data):
        """创建价格记录"""
        current_price = product_data.get('price')
        was_price = product_data.get('was_price')

        # 如果有促销价，说明正在促销
        if was_price and was_price > current_price:
            is_on_sale = True
            original_price = was_price
            discount_percentage = product_data.get('discount_percent', 0)
        else:
            is_on_sale = False
            original_price = current_price
            discount_percentage = 0

        return {
            'date': date,
            'price': current_price,
            'original_price': original_price,
            'is_on_sale': is_on_sale,
            'discount_percentage': discount_percentage,
            'status': product_data.get('status', 'success')
        }

    def save_history(self):
        """保存历史数据"""
        try:
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(self.history, f, ensure_ascii=False, indent=2)
            print(f'✅ 历史数据已保存: {len(self.history)} 个产品')
            return True
        except Exception as e:
            print(f'❌ 保存历史数据失败: {e}')
            return False

    def get_product_history(self, product_id, start_date=None, end_date=None):
        """获取产品的历史价格"""
        if product_id not in self.history:
            return []

        history = self.history[product_id]['price_history']

        if not start_date and not end_date:
            return history

        # 筛选日期范围
        filtered = []
        for record in history:
            record_date = record['date']
            if start_date and record_date < start_date:
                continue
            if end_date and record_date > end_date:
                continue
            filtered.append(record)

        return filtered

    def get_all_products(self):
        """获取所有产品列表"""
        products = []
        for product_id, data in self.history.items():
            products.append({
                'id': product_id,
                'name': data['product_name'],
                'brand': data['brand'],
                'category': data['category'],
                'url': data['url'],
                'price_count': len(data['price_history'])
            })
        return products

    def get_latest_prices(self):
        """获取所有产品的最新价格"""
        latest = {}
        for product_id, data in self.history.items():
            if data['price_history']:
                latest_record = data['price_history'][-1]
                latest[product_id] = {
                    'name': data['product_name'],
                    'brand': data['brand'],
                    'category': data['category'],
                    'date': latest_record['date'],
                    'price': latest_record['price'],
                    'is_on_sale': latest_record['is_on_sale'],
                    'discount_percentage': latest_record.get('discount_percentage', 0)
                }
        return latest

    def get_statistics(self):
        """获取统计信息"""
        total_products = len(self.history)
        brands = set()
        categories = set()
        total_records = 0

        for data in self.history.values():
            brands.add(data['brand'])
            categories.add(data['category'])
            total_records += len(data['price_history'])

        return {
            'total_products': total_products,
            'total_brands': len(brands),
            'total_categories': len(categories),
            'total_records': total_records,
            'brands': sorted(list(brands)),
            'categories': sorted(list(categories))
        }


if __name__ == '__main__':
    # 测试代码
    manager = PriceHistoryManager()

    # 测试添加产品
    test_product = {
        'name': 'eufyCam S330',
        'brand': 'eufy',
        'category': 'Security Camera',
        'url': 'https://www.jbhifi.com.au/products/eufy-s330',
        'price': 299,
        'was_price': 349,
        'discount_percent': 14,
        'status': 'success'
    }

    product_id = manager.update_price(test_product)
    print(f'\n产品ID: {product_id}')

    manager.save_history()

    # 显示统计
    stats = manager.get_statistics()
    print(f'\n统计信息:')
    print(f'  总产品数: {stats["total_products"]}')
    print(f'  品牌数: {stats["total_brands"]}')
    print(f'  品类数: {stats["total_categories"]}')
    print(f'  总记录数: {stats["total_records"]}')
