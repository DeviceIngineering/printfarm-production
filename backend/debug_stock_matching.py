#!/usr/bin/env python
"""
Отладка сопоставления товаров и остатков по ID
"""
import os
import sys
import django

# Настройка Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.sync.moysklad_client import MoySkladClient

def main():
    print("=== Отладка сопоставления товаров и остатков ===\n")
    
    client = MoySkladClient()
    target_article = '320-42802'
    warehouse_id = '241ed919-a631-11ee-0a80-07a9000bb947'
    
    try:
        print("1. Получаем список товаров...")
        
        # Получаем все товары
        params = {'limit': 1000, 'archived': False}
        all_products_data = client._make_request('GET', 'entity/product', params=params)
        all_products = all_products_data.get('rows', [])
        
        # Ищем наш товар в списке товаров
        target_product = None
        for product in all_products:
            if product.get('article') == target_article:
                target_product = product
                break
        
        if target_product:
            print(f"✅ Товар найден в списке товаров:")
            print(f"  ID: {target_product.get('id')}")
            print(f"  Артикул: {target_product.get('article')}")
            print(f"  Название: {target_product.get('name', '')[:50]}...")
        else:
            print(f"❌ Товар {target_article} не найден в списке товаров")
            return
        
        print("\n2. Получаем отчет по остаткам...")
        
        # Получаем отчет по остаткам
        store_href = f"{client.base_url}/entity/store/{warehouse_id}"
        stock_params = {
            'filter': f'store={store_href}',
            'limit': 1000,
            'includeZeroStocks': True
        }
        
        stock_data = client._make_request('GET', 'report/stock/all', params=stock_params)
        stock_rows = stock_data.get('rows', [])
        
        print(f"✅ Получено {len(stock_rows)} записей об остатках")
        
        # Ищем наш товар в отчете по остаткам
        target_stock = None
        for stock_row in stock_rows:
            # Извлекаем ID товара из href
            meta = stock_row.get('meta', {})
            href = meta.get('href', '')
            if href:
                product_id = href.split('/')[-1]
                if product_id == target_product['id']:
                    target_stock = stock_row
                    break
        
        if target_stock:
            print(f"✅ Товар найден в отчете по остаткам:")
            print(f"  ID из href: {target_stock.get('meta', {}).get('href', '').split('/')[-1]}")
            print(f"  Остаток: {target_stock.get('stock', 0)}")
        else:
            print(f"❌ Товар не найден в отчете по остаткам")
            print(f"Ищем товар по артикулу в отчете...")
            
            # Поиск по артикулу
            for stock_row in stock_rows:
                if stock_row.get('article') == target_article:
                    print(f"✅ Найден по артикулу:")
                    print(f"  ID из href: {stock_row.get('meta', {}).get('href', '').split('/')[-1]}")
                    print(f"  Остаток: {stock_row.get('stock', 0)}")
                    target_stock = stock_row
                    break
        
        print("\n3. Сравнение ID:")
        product_id_from_list = target_product.get('id')
        stock_id_from_href = target_stock.get('meta', {}).get('href', '').split('/')[-1] if target_stock else None
        
        print(f"ID товара из списка: {product_id_from_list}")
        print(f"ID товара из остатков: {stock_id_from_href}")
        
        if product_id_from_list == stock_id_from_href:
            print("✅ ID совпадают")
        else:
            print("❌ ID НЕ совпадают! Это причина проблемы")
        
        print("\n4. Проверка через обычный get_stock_report:")
        
        # Используем обычный метод get_stock_report
        normal_stock = client.get_stock_report(warehouse_id, [])
        
        target_in_normal = None
        for item in normal_stock:
            if item.get('article') == target_article:
                target_in_normal = item
                break
        
        if target_in_normal:
            print(f"✅ Товар найден через get_stock_report:")
            print(f"  Остаток: {target_in_normal.get('stock', 0)}")
        else:
            print("❌ Товар не найден через get_stock_report")
        
        print("\n5. Рекомендация:")
        if normal_stock and any(item.get('article') == target_article for item in normal_stock):
            print("🔧 Рекомендуется использовать get_stock_report вместо get_all_products_with_stock")
            print("   для получения корректных остатков")
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()