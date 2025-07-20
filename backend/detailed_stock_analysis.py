#!/usr/bin/env python
"""
Детальный анализ остатков по складу для товара 376-41401
"""
import os
import sys
import django
import json

# Настройка Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.sync.moysklad_client import MoySkladClient

def main():
    print("=== Детальный анализ остатков по товару 376-41401 ===\n")
    
    client = MoySkladClient()
    warehouse_id = '241ed919-a631-11ee-0a80-07a9000bb947'
    
    print("1. Получение ВСЕХ остатков по складу (без фильтрации)...")
    try:
        all_stock_data = client.get_stock_report(warehouse_id, [])  # Пустой список = без исключений
        print(f"✅ Получено {len(all_stock_data)} товаров с остатками (всего)")
        
        # Ищем товар 376-41401
        found_product = None
        for item in all_stock_data:
            if item.get('article') == '376-41401':
                found_product = item
                break
        
        if found_product:
            print(f"\n✅ Товар 376-41401 НАЙДЕН в полном списке остатков!")
            print(f"  Артикул: {found_product.get('article')}")
            print(f"  Название: {found_product.get('name')}")
            print(f"  Остаток: {found_product.get('stock', 0)}")
            print(f"  Резерв: {found_product.get('reserve', 0)}")
            print(f"  В пути: {found_product.get('inTransit', 0)}")
            print(f"  Доступно: {found_product.get('quantity', 0)}")
            
            # Анализ группы товара
            folder = found_product.get('folder')
            if folder:
                folder_meta = folder.get('meta', {})
                folder_href = folder_meta.get('href', '')
                if folder_href:
                    folder_id = folder_href.split('/')[-1]
                    print(f"  Группа ID: {folder_id}")
                    
                    # Получаем информацию о группе
                    try:
                        folder_response = client._make_request('GET', f'entity/productfolder/{folder_id}')
                        print(f"  Группа: {folder_response.get('name')}")
                        print(f"  Полный путь: {folder_response.get('pathName', 'Не указан')}")
                    except Exception as e:
                        print(f"  ❌ Ошибка получения группы: {e}")
        else:
            print("❌ Товар 376-41401 НЕ найден даже в полном списке остатков")
            print("Это означает, что:")
            print("  - У товара нулевой остаток на этом складе")
            print("  - Товар не привязан к этому складу")
            print("  - Товар архивирован или удален")
    except Exception as e:
        print(f"❌ Ошибка получения остатков: {e}")
    
    print("\n2. Прямой запрос информации о товаре...")
    try:
        # Получаем информацию о товаре напрямую по ID
        product_id = '03d80ab8-7a3d-11ef-0a80-040c003525fc'
        product_info = client._make_request('GET', f'entity/product/{product_id}')
        
        print(f"✅ Информация о товаре:")
        print(f"  ID: {product_info.get('id')}")
        print(f"  Название: {product_info.get('name')}")
        print(f"  Артикул: {product_info.get('article')}")
        print(f"  Архивирован: {product_info.get('archived', False)}")
        print(f"  Обновлен: {product_info.get('updated')}")
        
        # Проверяем остатки конкретно этого товара
        print(f"\n3. Запрос остатков конкретно для товара {product_id}...")
        
        # Формируем фильтр для конкретного товара
        product_href = f"https://api.moysklad.ru/api/remap/1.2/entity/product/{product_id}"
        store_href = f"https://api.moysklad.ru/api/remap/1.2/entity/store/{warehouse_id}"
        
        params = {
            'filter': f'store={store_href};assortment={product_href}',
            'limit': 10
        }
        
        stock_response = client._make_request('GET', 'report/stock/all', params=params)
        stock_rows = stock_response.get('rows', [])
        
        if stock_rows:
            stock_item = stock_rows[0]
            print(f"✅ Остатки товара на складе:")
            print(f"  Остаток: {stock_item.get('stock', 0)}")
            print(f"  Резерв: {stock_item.get('reserve', 0)}")
            print(f"  В пути: {stock_item.get('inTransit', 0)}")
            print(f"  Доступно: {stock_item.get('quantity', 0)}")
            
            if stock_item.get('stock', 0) == 0:
                print(f"  ⚠️ ПРИЧИНА НАЙДЕНА: У товара нулевой остаток на складе!")
                print(f"  Товар не включается в синхронизацию, так как остаток = 0")
        else:
            print(f"❌ Остатки товара на складе не найдены")
            print(f"Возможно товар не привязан к складу {warehouse_id}")
    except Exception as e:
        print(f"❌ Ошибка получения информации о товаре: {e}")
    
    print("\n4. Проверка всех складов, к которым привязан товар...")
    try:
        # Получаем список всех складов
        warehouses = client.get_warehouses()
        print(f"Проверяем товар на {len(warehouses)} складах:")
        
        found_on_warehouses = []
        
        for warehouse in warehouses:
            if warehouse.get('archived'):
                continue
                
            try:
                wh_id = warehouse['id']
                wh_name = warehouse['name']
                
                # Проверяем остатки на этом складе
                product_href = f"https://api.moysklad.ru/api/remap/1.2/entity/product/{product_id}"
                store_href = f"https://api.moysklad.ru/api/remap/1.2/entity/store/{wh_id}"
                
                params = {
                    'filter': f'store={store_href};assortment={product_href}',
                    'limit': 1
                }
                
                stock_response = client._make_request('GET', 'report/stock/all', params=params)
                stock_rows = stock_response.get('rows', [])
                
                if stock_rows and stock_rows[0].get('stock', 0) > 0:
                    stock_value = stock_rows[0].get('stock', 0)
                    found_on_warehouses.append((wh_name, wh_id, stock_value))
                    print(f"  ✅ {wh_name}: {stock_value} шт.")
                else:
                    print(f"  ❌ {wh_name}: остаток 0 или нет данных")
                    
            except Exception as e:
                print(f"  ❌ {warehouse['name']}: ошибка - {e}")
        
        if found_on_warehouses:
            print(f"\n✅ Товар найден на складах:")
            for wh_name, wh_id, stock in found_on_warehouses:
                print(f"  - {wh_name} ({wh_id}): {stock} шт.")
            
            print(f"\n⚠️ РЕКОМЕНДАЦИЯ:")
            print(f"Возможно нужно изменить склад по умолчанию в настройках")
            print(f"или добавить товар на склад '{warehouses[0]['name']}'")
        else:
            print(f"\n❌ Товар не найден ни на одном складе с остатком > 0")
    except Exception as e:
        print(f"❌ Ошибка проверки складов: {e}")

if __name__ == '__main__':
    main()