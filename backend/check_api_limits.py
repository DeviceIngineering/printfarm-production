#!/usr/bin/env python3
"""
Check API limits and data completeness.
"""
import os
import sys
import django

# Setup Django
sys.path.append('/Users/dim11/Documents/myProjects/Factory_v2/backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()

from apps.sync.moysklad_client import MoySkladClient
from apps.products.models import Product

def check_api_limits():
    """Check API limits and data completeness."""
    
    print("=== ПРОВЕРКА ОГРАНИЧЕНИЙ API ===")
    
    client = MoySkladClient()
    warehouse_id = '241ed919-a631-11ee-0a80-07a9000bb947'
    
    print("Загружаем отчет об остатках...")
    stock_data = client.get_stock_report(warehouse_id)
    print(f"Получено записей из отчета об остатках: {len(stock_data)}")
    
    print()
    print("Анализируем данные...")
    # Фильтруем только товары (не услуги и не архивные)
    products_in_stock = []
    archived_count = 0
    non_product_count = 0
    
    for item in stock_data:
        meta = item.get('meta', {})
        if meta.get('type') != 'product':
            non_product_count += 1
            continue
        
        if item.get('archived', False):
            archived_count += 1
            continue
            
        products_in_stock.append(item)
    
    print(f"Всего записей в отчете: {len(stock_data)}")
    print(f"Не товары (услуги и др.): {non_product_count}")
    print(f"Архивные товары: {archived_count}")
    print(f"Активные товары: {len(products_in_stock)}")
    
    print()
    print("=== ТОВАРЫ В БАЗЕ ДАННЫХ ===")
    print(f"Товаров в БД: {Product.objects.count()}")
    print(f"С изображениями: {Product.objects.filter(images__isnull=False).distinct().count()}")
    print(f"Без изображений: {Product.objects.filter(images__isnull=True).count()}")
    
    print()
    print("=== ПРОВЕРКА ПОЛУЧЕНИЯ ИЗОБРАЖЕНИЙ ===")
    
    # Найдем несколько товаров с изображениями и проверим их
    products_with_images = Product.objects.filter(images__isnull=False).distinct()[:5]
    
    for i, product in enumerate(products_with_images, 1):
        print(f"{i}. {product.article}: {product.name[:50]}...")
        print(f"   Изображений в БД: {product.images.count()}")
        
        # Проверим, сколько изображений есть в МойСклад
        try:
            images_data = client.get_product_images(product.moysklad_id)
            print(f"   Изображений в МойСклад: {len(images_data)}")
            
            if len(images_data) != product.images.count():
                print(f"   ⚠️ НЕСООТВЕТСТВИЕ! В МойСклад {len(images_data)}, в БД {product.images.count()}")
                
        except Exception as e:
            print(f"   ❌ Ошибка получения изображений: {str(e)}")
    
    print()
    print("=== ПРОВЕРКА ЛИМИТОВ API ===")
    
    # Проверим лимиты для отчетов
    print("Проверяем лимиты отчета об остатках...")
    
    # Запросим с разными лимитами
    for limit in [100, 500, 1000, 1500]:
        try:
            # Создадим временный клиент с другим лимитом
            temp_client = MoySkladClient()
            store_href = f"{temp_client.base_url}/entity/store/{warehouse_id}"
            params = {
                'filter': f'store={store_href}',
                'limit': limit
            }
            
            data = temp_client._make_request('GET', 'report/stock/all', params=params)
            rows_count = len(data.get('rows', []))
            
            print(f"Лимит {limit}: получено {rows_count} записей")
            
            if rows_count < limit:
                print(f"  ✅ Все данные получены (меньше лимита)")
                break
            else:
                print(f"  ⚠️ Возможно есть еще данные (достигнут лимит)")
                
        except Exception as e:
            print(f"Лимит {limit}: ❌ Ошибка - {str(e)}")

if __name__ == '__main__':
    check_api_limits()