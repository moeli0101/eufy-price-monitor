#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
促销日历生成器
生成月度促销日历、对比分析和文本导出
"""

import json
from datetime import datetime, timedelta
from collections import defaultdict
from pathlib import Path


class PromotionCalendarGenerator:
    def __init__(self, history_file='price_history.json', promotions_file='promotions.json'):
        self.history_file = history_file
        self.promotions_file = promotions_file
        self.history = {}
        self.promotions = {}
        self.load_data()

    def load_data(self):
        """加载历史和促销数据"""
        if Path(self.history_file).exists():
            with open(self.history_file, 'r', encoding='utf-8') as f:
                self.history = json.load(f)

        if Path(self.promotions_file).exists():
            with open(self.promotions_file, 'r', encoding='utf-8') as f:
                self.promotions = json.load(f)

    def generate_monthly_calendar(self, year, month, product_ids=None, brands=None, categories=None):
        """生成月度促销日历"""
        calendar_data = {}

        # 获取月份的天数
        if month == 12:
            next_month = datetime(year + 1, 1, 1)
        else:
            next_month = datetime(year, month + 1, 1)
        days_in_month = (next_month - datetime(year, month, 1)).days

        # 筛选产品
        products_to_include = self._filter_products(product_ids, brands, categories)

        for product_id in products_to_include:
            if product_id not in self.history:
                continue

            product_data = self.history[product_id]
            calendar_data[product_id] = {
                'product_name': product_data['product_name'],
                'brand': product_data['brand'],
                'category': product_data['category'],
                'url': product_data.get('url', ''),
                'days': {}
            }

            # 遍历该月的每一天
            for day in range(1, days_in_month + 1):
                date_str = f"{year}-{month:02d}-{day:02d}"

                # 查找该日期的价格记录
                price_record = self._find_price_on_date(product_data['price_history'], date_str)

                if price_record:
                    calendar_data[product_id]['days'][day] = {
                        'date': date_str,
                        'price': price_record['price'],
                        'original_price': price_record['original_price'],
                        'is_sale': price_record['is_on_sale'],
                        'discount': price_record.get('discount_percentage', 0)
                    }

        return calendar_data

    def _filter_products(self, product_ids=None, brands=None, categories=None):
        """筛选产品"""
        if product_ids:
            return product_ids

        filtered = []
        for product_id, data in self.history.items():
            if brands and data['brand'] not in brands:
                continue
            if categories and data['category'] not in categories:
                continue
            filtered.append(product_id)

        return filtered

    def _find_price_on_date(self, price_history, target_date):
        """查找指定日期的价格记录"""
        for record in price_history:
            if record['date'] == target_date:
                return record
        return None

    def generate_comparison_view(self, product_ids, start_date, end_date):
        """生成对比视图"""
        comparison = {
            'period': {
                'start': start_date,
                'end': end_date
            },
            'products': [],
            'overlap_analysis': {}
        }

        for product_id in product_ids:
            if product_id not in self.history:
                continue

            product_data = self.history[product_id]
            prices = []
            promotions = []

            # 获取时间段内的价格
            for record in product_data['price_history']:
                if start_date <= record['date'] <= end_date:
                    prices.append(record)
                    if record['is_on_sale']:
                        promotions.append({
                            'date': record['date'],
                            'discount': record.get('discount_percentage', 0)
                        })

            # 计算统计数据
            if prices:
                avg_price = sum(p['price'] for p in prices) / len(prices)
                min_price = min(p['price'] for p in prices)
                max_price = max(p['price'] for p in prices)
            else:
                avg_price = min_price = max_price = 0

            comparison['products'].append({
                'id': product_id,
                'name': product_data['product_name'],
                'brand': product_data['brand'],
                'category': product_data['category'],
                'prices': prices,
                'promotions': promotions,
                'promotion_days': len(promotions),
                'avg_discount': round(sum(p['discount'] for p in promotions) / len(promotions), 1) if promotions else 0,
                'avg_price': round(avg_price, 2),
                'min_price': min_price,
                'max_price': max_price
            })

        # 分析促销重叠
        comparison['overlap_analysis'] = self._analyze_overlap(comparison['products'], start_date, end_date)

        return comparison

    def _analyze_overlap(self, products, start_date, end_date):
        """分析促销重叠"""
        # 为每一天创建促销产品列表
        daily_promotions = defaultdict(list)

        for product in products:
            for promo in product['promotions']:
                daily_promotions[promo['date']].append(product['id'])

        # 统计
        overlap_days = sum(1 for products_list in daily_promotions.values() if len(products_list) > 1)
        total_promo_days = len(daily_promotions)

        return {
            'total_promotion_days': total_promo_days,
            'overlap_days': overlap_days,
            'overlap_percentage': round(overlap_days / total_promo_days * 100, 1) if total_promo_days > 0 else 0,
            'daily_promotions': dict(daily_promotions)
        }

    def export_text_format(self, calendar_data, output_file='promotion_calendar.txt'):
        """导出文本格式"""
        lines = []
        lines.append('促销日历导出')
        lines.append('=' * 80)
        lines.append('')

        for product_id, data in calendar_data.items():
            lines.append(f"产品：{data['product_name']} ({data['brand']})")
            lines.append(f"品类：{data['category']}")
            lines.append('-' * 80)

            if not data['days']:
                lines.append('  暂无数据')
            else:
                for day, day_data in sorted(data['days'].items()):
                    status = f"🔥 促销 ({day_data['discount']}% OFF)" if day_data['is_sale'] else "正常价格"
                    price_str = f"${day_data['price']}"
                    if day_data['is_sale']:
                        price_str += f" (原价 ${day_data['original_price']})"
                    lines.append(f"  {day_data['date']}: {price_str} - {status}")

            lines.append('')

        text_content = '\n'.join(lines)

        # 保存到文件
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(text_content)

        print(f'✅ 文本日历已导出到: {output_file}')
        return text_content

    def export_comparison_text(self, comparison, output_file='promotion_comparison.txt'):
        """导出对比文本"""
        lines = []
        lines.append('促销对比分析')
        lines.append('=' * 80)
        lines.append(f"时间段: {comparison['period']['start']} 至 {comparison['period']['end']}")
        lines.append('')

        for product in comparison['products']:
            lines.append(f"产品：{product['name']} ({product['brand']})")
            lines.append('-' * 80)
            lines.append(f"  促销天数：{product['promotion_days']} 天")
            lines.append(f"  平均折扣：{product['avg_discount']}%")
            lines.append(f"  平均价格：${product['avg_price']}")
            lines.append(f"  最低价格：${product['min_price']}")
            lines.append(f"  最高价格：${product['max_price']}")
            lines.append('')

        lines.append('促销重叠分析:')
        lines.append('-' * 80)
        overlap = comparison['overlap_analysis']
        lines.append(f"  总促销天数：{overlap['total_promotion_days']} 天")
        lines.append(f"  重叠天数：{overlap['overlap_days']} 天")
        lines.append(f"  重叠比例：{overlap['overlap_percentage']}%")
        lines.append('')

        text_content = '\n'.join(lines)

        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(text_content)

        print(f'✅ 对比文本已导出到: {output_file}')
        return text_content

    def save_calendar_json(self, calendar_data, output_file='promotion_calendar.json'):
        """保存日历数据为JSON"""
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(calendar_data, f, ensure_ascii=False, indent=2)
        print(f'✅ 日历数据已保存到: {output_file}')


if __name__ == '__main__':
    # 测试代码
    generator = PromotionCalendarGenerator()

    # 生成当月日历
    now = datetime.now()
    calendar = generator.generate_monthly_calendar(now.year, now.month)

    print(f'生成了 {len(calendar)} 个产品的日历')

    # 保存
    generator.save_calendar_json(calendar)

    # 导出文本
    if calendar:
        generator.export_text_format(calendar)
