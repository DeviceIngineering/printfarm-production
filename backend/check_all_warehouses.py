#!/usr/bin/env python
"""
Проверка остатков товара 320-42802 на всех складах
"""
import os
import sys
import django

# Настройка Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.sync.moysklad_client import MoySkladClient

def main():
    print("=== Проверка остатков товара 320-42802 на всех складах ===\n")
    
    client = MoySkladClient()
    target_article = '320-42802'
    
    try:
        # Получаем все склады
        print("1. Получаем список всех складов...")
        warehouses = client.get_warehouses()
        
        print(f"✅ Найдено {len(warehouses)} складов")
        
        # Проверяем остатки на каждом складе
        print("\n2. Проверяем остатки товара на каждом складе:")
        
        total_stock = 0
        found_warehouses = []
        
        for warehouse in warehouses:
            if warehouse.get('archived'):
                print(f"⏸️  {warehouse['name']} - архивный, пропускаем")
                continue
            
            print(f"\n📦 Склад: {warehouse['name']} ({warehouse['id']})")
            
            try:
                # Используем обычный отчет по остаткам (может показать другие данные)
                stock_data = client.get_stock_report(warehouse['id'], [])
                
                # Ищем товар
                found = False
                for item in stock_data:
                    if item.get('article') == target_article:
                        found = True
                        stock = item.get('stock', 0)
                        print(f"  ✅ Найден! Остаток: {stock} шт.")
                        if stock > 0:
                            total_stock += stock
                            found_warehouses.append({
                                'warehouse': warehouse['name'],
                                'stock': stock
                            })
                        break
                
                if not found:
                    print(f"  ❌ Товар не найден в отчете по остаткам")
                    
                    # Попробуем через get_all_products_with_stock
                    try:
                        groups = client.get_product_groups()
                        all_products = client.get_all_products_with_stock(warehouse['id'], [])
                        
                        for product in all_products:
                            if product.get('article') == target_article:
                                stock = product.get('stock', 0)
                                print(f"  📋 Через get_all_products_with_stock: {stock} шт.")
                                if stock > 0:
                                    total_stock += stock
                                    found_warehouses.append({
                                        'warehouse': warehouse['name'],
                                        'stock': stock
                                    })
                                break
                    except Exception as e:
                        print(f"  ⚠️  Ошибка get_all_products_with_stock: {e}")
                        
            except Exception as e:
                print(f"  ❌ Ошибка получения остатков: {e}")
        
        print(f"\n3. Итоговые результаты:")
        print(f"Общий остаток товара {target_article}: {total_stock} шт.")
        
        if found_warehouses:
            print("Склады с положительными остатками:")
            for item in found_warehouses:
                print(f"  - {item['warehouse']}: {item['stock']} шт.")
        else:
            print("❌ Товар не найден ни на одном складе с положительным остатком")
        
        # Дополнительная проверка через прямой запрос к API
        print("\n4. Дополнительная проверка через прямой API запрос...")
        
        try:
            # Попробуем найти товар через поиск
            params = {
                'search': target_article,
                'limit': 10
            }
            
            product_data = client._make_request('GET', 'entity/product', params=params)
            products = product_data.get('rows', [])
            
            if products:
                for product in products:
                    if product.get('article') == target_article:
                        print(f"✅ Товар найден в справочнике:")
                        print(f"  ID: {product.get('id')}")
                        print(f"  Название: {product.get('name', '')[:50]}...")
                        
                        # Получаем остатки для этого товара
                        try:
                            product_id = product.get('id')
                            stock_params = {
                                'filter': f'product.id={product_id}',
                                'limit': 100
                            }
                            
                            stock_report = client._make_request('GET', 'report/stock/all', params=stock_params)
                            stock_rows = stock_report.get('rows', [])
                            
                            if stock_rows:
                                print("  Остатки по складам:")
                                for row in stock_rows:
                                    store_name = row.get('store', {}).get('name', 'Неизвестный склад')
                                    stock = row.get('stock', 0)
                                    print(f"    - {store_name}: {stock} шт.")
                            else:
                                print("  ❌ Остатки не найдены")
                                
                        except Exception as e:
                            print(f"  ⚠️  Ошибка получения остатков по товару: {e}")
                        
                        break
            else:
                print(f"❌ Товар {target_article} не найден через поиск")
                
        except Exception as e:
            print(f"❌ Ошибка прямого запроса: {e}")
        
    except Exception as e:
        print(f"❌ Общая ошибка: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()