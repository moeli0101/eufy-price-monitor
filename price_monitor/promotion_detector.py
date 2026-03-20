#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
促销检测器
检测产品的促销活动，记录促销的开始、结束和持续时间
"""

import json
from datetime import datetime, timedelta
from pathlib import Path


class PromotionDetector:
    def __init__(self, promotions_file='promotions.json'):
        self.promotions_file = promotions_file
        self.promotions = {
            'active_promotions': [],
            'historical_promotions': []
        }
        self.load_promotions()

    def load_promotions(self):
        """加载促销记录"""
        if Path(self.promotions_file).exists():
            try:
                with open(self.promotions_file, 'r', encoding='utf-8') as f:
                    self.promotions = json.load(f)
                print(f'✅ 加载促销记录: {len(self.promotions["active_promotions"])} 活跃, '
                      f'{len(self.promotions["historical_promotions"])} 历史')
            except Exception as e:
                print(f'⚠️  加载促销记录失败: {e}')
                self.promotions = {
                    'active_promotions': [],
                    'historical_promotions': []
                }
        else:
            print('📝 首次运行，创建新的促销记录文件')

    def detect_promotion(self, product_id, product_name, brand, current_price, original_price):
        """检测是否是促销"""
        if not current_price or not original_price:
            return None

        # 计算折扣
        if original_price > current_price:
            discount = ((original_price - current_price) / original_price) * 100
            save_amount = original_price - current_price

            # 折扣大于5%认为是促销
            if discount >= 5:
                return {
                    'is_promotion': True,
                    'discount_percentage': round(discount, 1),
                    'save_amount': round(save_amount, 2),
                    'original_price': original_price,
                    'sale_price': current_price
                }

        return {'is_promotion': False}

    def update_promotions(self, product_id, product_name, brand, category,
                         current_price, original_price, url=''):
        """更新促销状态"""
        today = datetime.now().strftime("%Y-%m-%d")

        # 检测促销
        promotion_info = self.detect_promotion(
            product_id, product_name, brand,
            current_price, original_price
        )

        if not promotion_info:
            return

        if promotion_info['is_promotion']:
            # 检查是否有活跃的促销
            active = self._get_active_promotion(product_id)

            if not active:
                # 新促销开始
                new_promotion = {
                    'product_id': product_id,
                    'product_name': product_name,
                    'brand': brand,
                    'category': category,
                    'url': url,
                    'start_date': today,
                    'end_date': None,
                    'original_price': original_price,
                    'sale_price': current_price,
                    'discount_percentage': promotion_info['discount_percentage'],
                    'save_amount': promotion_info['save_amount'],
                    'duration_days': 1,
                    'status': 'active'
                }
                self.promotions['active_promotions'].append(new_promotion)
                print(f'  🔥 新促销: {product_name} ({promotion_info["discount_percentage"]}% OFF)')
            else:
                # 更新现有促销
                start_date = datetime.strptime(active['start_date'], "%Y-%m-%d")
                today_date = datetime.strptime(today, "%Y-%m-%d")
                duration = (today_date - start_date).days + 1

                active['duration_days'] = duration
                active['sale_price'] = current_price
                active['discount_percentage'] = promotion_info['discount_percentage']
                active['save_amount'] = promotion_info['save_amount']
        else:
            # 不是促销，检查是否有活跃促销需要结束
            active = self._get_active_promotion(product_id)
            if active:
                # 促销结束
                active['end_date'] = today
                active['status'] = 'ended'

                # 移到历史记录
                self.promotions['historical_promotions'].append(active)
                self.promotions['active_promotions'].remove(active)

                print(f'  ✅ 促销结束: {product_name} (持续 {active["duration_days"]} 天)')

    def _get_active_promotion(self, product_id):
        """获取产品的活跃促销"""
        for promo in self.promotions['active_promotions']:
            if promo['product_id'] == product_id:
                return promo
        return None

    def save_promotions(self):
        """保存促销记录"""
        try:
            with open(self.promotions_file, 'w', encoding='utf-8') as f:
                json.dump(self.promotions, f, ensure_ascii=False, indent=2)
            print(f'✅ 促销记录已保存')
            return True
        except Exception as e:
            print(f'❌ 保存促销记录失败: {e}')
            return False

    def get_active_promotions(self, brand=None, category=None):
        """获取活跃促销"""
        promotions = self.promotions['active_promotions']

        if brand:
            promotions = [p for p in promotions if p['brand'].lower() == brand.lower()]

        if category:
            promotions = [p for p in promotions if p['category'] == category]

        return promotions

    def get_promotion_history(self, product_id=None, start_date=None, end_date=None):
        """获取促销历史"""
        history = self.promotions['historical_promotions'].copy()

        if product_id:
            history = [p for p in history if p['product_id'] == product_id]

        if start_date:
            history = [p for p in history if p['start_date'] >= start_date]

        if end_date:
            history = [p for p in history if p['end_date'] and p['end_date'] <= end_date]

        return history

    def get_statistics(self):
        """获取促销统计"""
        active = self.promotions['active_promotions']
        historical = self.promotions['historical_promotions']

        stats = {
            'active_count': len(active),
            'historical_count': len(historical),
            'avg_discount_active': 0,
            'avg_duration_historical': 0,
            'brands_on_sale': set(),
            'categories_on_sale': set()
        }

        if active:
            stats['avg_discount_active'] = round(
                sum(p['discount_percentage'] for p in active) / len(active), 1
            )
            stats['brands_on_sale'] = set(p['brand'] for p in active)
            stats['categories_on_sale'] = set(p['category'] for p in active)

        if historical:
            stats['avg_duration_historical'] = round(
                sum(p['duration_days'] for p in historical) / len(historical), 1
            )

        # 转换 set 为 list
        stats['brands_on_sale'] = sorted(list(stats['brands_on_sale']))
        stats['categories_on_sale'] = sorted(list(stats['categories_on_sale']))

        return stats


if __name__ == '__main__':
    # 测试代码
    detector = PromotionDetector()

    # 测试检测促销
    product_id = 'eufy_eufycam_s330'
    detector.update_promotions(
        product_id=product_id,
        product_name='eufyCam S330',
        brand='eufy',
        category='Security Camera',
        current_price=299,
        original_price=349,
        url='https://example.com'
    )

    detector.save_promotions()

    # 显示统计
    stats = detector.get_statistics()
    print(f'\n促销统计:')
    print(f'  活跃促销: {stats["active_count"]}')
    print(f'  历史促销: {stats["historical_count"]}')
    print(f'  平均折扣: {stats["avg_discount_active"]}%')
