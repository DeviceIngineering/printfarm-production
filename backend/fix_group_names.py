#!/usr/bin/env python
"""
Исправление названий групп для существующих товаров
"""
import os
import sys
import django

# Настройка Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.sync.moysklad_client import MoySkladClient
from apps.products.models import Product

def main():
    print("=== Исправление названий групп ===\n")
    
    client = MoySkladClient()
    
    try:
        # Получаем группы из МойСклад
        print("1. Загружаем группы товаров из МойСклад...")
        groups = client.get_product_groups()
        groups_dict = {group['id']: group['name'] for group in groups}
        
        print(f"✅ Загружено {len(groups_dict)} групп")
        
        # Получаем товары с пустыми названиями групп
        print("\n2. Ищем товары с пустыми названиями групп...")
        products_to_fix = Product.objects.filter(
            product_group_name='',
            product_group_id__isnull=False
        ).exclude(product_group_id='')
        
        print(f"✅ Найдено {products_to_fix.count()} товаров для исправления")
        
        # Исправляем названия групп
        print("\n3. Исправляем названия групп...")
        fixed_count = 0
        
        for product in products_to_fix:
            group_name = groups_dict.get(product.product_group_id, '')
            if group_name:
                product.product_group_name = group_name
                product.save()
                fixed_count += 1
                print(f"✅ {product.article}: {group_name}")
            else:
                print(f"⚠️  {product.article}: группа с ID {product.product_group_id} не найдена")
        
        print(f"\n📊 Результат: исправлено {fixed_count} товаров")
        
        # Проверяем результат
        print("\n4. Проверка результата...")
        podiums_count = Product.objects.filter(product_group_name__icontains='Подиумы').count()
        print(f"✅ Товаров группы 'Подиумы': {podiums_count}")
        
        if podiums_count > 0:
            print("\nТовары группы 'Подиумы':")
            for product in Product.objects.filter(product_group_name__icontains='Подиумы').order_by('article'):
                print(f"  📦 {product.article}: {product.name[:50]}... (остаток: {product.current_stock})")
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()