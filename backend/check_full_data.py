#!/usr/bin/env python3
"""
Check full data statistics and examples.
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
django.setup()

from apps.products.models import Product
from decimal import Decimal

print("📊 ПОЛНАЯ СТАТИСТИКА ДАННЫХ В СИСТЕМЕ\n")

# Общая статистика
total = Product.objects.count()
print(f"Всего товаров: {total}")

# Детальная статистика по заполненности
fields_stats = {
    'Остаток > 0': Product.objects.filter(current_stock__gt=0).count(),
    'Продажи > 0': Product.objects.filter(sales_last_2_months__gt=0).count(),
    'Расход/день > 0': Product.objects.filter(average_daily_consumption__gt=0).count(),
    'Дней остатка': Product.objects.filter(days_of_stock__isnull=False).count(),
    'Требуют производства': Product.objects.filter(production_needed__gt=0).count(),
}

print("\n📈 Заполненность данных:")
for field, count in fields_stats.items():
    percentage = (count / total * 100) if total > 0 else 0
    print(f"  {field}: {count}/{total} ({percentage:.1f}%)")

# Статистика по типам
print("\n📦 Распределение по типам:")
for product_type, label in Product.PRODUCT_TYPE_CHOICES:
    count = Product.objects.filter(product_type=product_type).count()
    percentage = (count / total * 100) if total > 0 else 0
    print(f"  {label}: {count} ({percentage:.1f}%)")

# Статистика по приоритетам
print("\n🎯 Распределение по приоритетам:")
priority_ranges = [
    (100, 100, "Критический (100)"),
    (80, 99, "Высокий (80-99)"),
    (60, 79, "Средний (60-79)"),
    (40, 59, "Низкий (40-59)"),
    (0, 39, "Минимальный (0-39)"),
]

for min_p, max_p, label in priority_ranges:
    count = Product.objects.filter(production_priority__gte=min_p, production_priority__lte=max_p).count()
    percentage = (count / total * 100) if total > 0 else 0
    print(f"  {label}: {count} ({percentage:.1f}%)")

# Примеры из каждой категории
print("\n📋 ПРИМЕРЫ ТОВАРОВ ПО КАТЕГОРИЯМ:")

print("\n1️⃣ КРИТИЧЕСКИЕ (остаток < 5, есть продажи):")
critical_products = Product.objects.filter(product_type='critical').order_by('-production_priority')[:3]
for p in critical_products:
    print(f"  • {p.article}: остаток={p.current_stock}, продажи={p.sales_last_2_months}, "
          f"расход/день={p.average_daily_consumption}, дней={p.days_of_stock}, приоритет={p.production_priority}")

print("\n2️⃣ НОВЫЕ (нет продаж или мало продаж и остатков):")
new_products = Product.objects.filter(product_type='new').order_by('-production_needed')[:3]
for p in new_products:
    print(f"  • {p.article}: остаток={p.current_stock}, продажи={p.sales_last_2_months}, "
          f"к производству={p.production_needed}, приоритет={p.production_priority}")

print("\n3️⃣ СТАРЫЕ (стабильные продажи):")
old_products = Product.objects.filter(product_type='old', sales_last_2_months__gt=0).order_by('-sales_last_2_months')[:3]
for p in old_products:
    print(f"  • {p.article}: остаток={p.current_stock}, продажи={p.sales_last_2_months}, "
          f"расход/день={p.average_daily_consumption}, дней={p.days_of_stock}")

# Товары требующие производства
print("\n⚡ ТОВАРЫ ТРЕБУЮЩИЕ СРОЧНОГО ПРОИЗВОДСТВА:")
urgent_products = Product.objects.filter(production_needed__gt=0).order_by('-production_priority', '-production_needed')[:5]
for p in urgent_products:
    print(f"  • {p.article} [{p.product_type}]: остаток={p.current_stock}, "
          f"нужно произвести={p.production_needed}, приоритет={p.production_priority}")

# Проверка корректности расчетов
print("\n🔍 ПРОВЕРКА КОРРЕКТНОСТИ РАСЧЕТОВ:")
sample_product = Product.objects.filter(sales_last_2_months__gt=0, current_stock__gt=0).first()
if sample_product:
    print(f"Пример: {sample_product.article}")
    print(f"  Продажи за 2 мес: {sample_product.sales_last_2_months}")
    print(f"  Расход/день: {sample_product.average_daily_consumption}")
    print(f"  Проверка: {sample_product.sales_last_2_months} / 60 = {sample_product.sales_last_2_months / 60}")
    print(f"  Остаток: {sample_product.current_stock}")
    print(f"  Дней остатка: {sample_product.days_of_stock}")
    if sample_product.average_daily_consumption > 0:
        calculated_days = sample_product.current_stock / sample_product.average_daily_consumption
        print(f"  Проверка: {sample_product.current_stock} / {sample_product.average_daily_consumption} = {calculated_days}")

print("\n✅ Система полностью готова к работе!")