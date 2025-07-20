#!/usr/bin/env python
"""
Анализ структуры данных товара из МойСклад
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
    print("=== Анализ структуры данных товара ===\n")
    
    client = MoySkladClient()
    
    # Получаем один товар для анализа структуры
    warehouse_id = '241ed919-a631-11ee-0a80-07a9000bb947'
    groups = client.get_product_groups()
    podiums_group = next(g for g in groups if g['name'] == 'Подиумы')
    excluded_groups = [g['id'] for g in groups if g['id'] != podiums_group['id']]
    
    products = client.get_all_products_with_stock(warehouse_id, excluded_groups)
    
    if products:
        print("=== Структура данных товара ===")
        product = products[0]
        print(json.dumps(product, indent=2, ensure_ascii=False))
        
        print("\n=== Информация о группе ===")
        if 'folder' in product:
            print("Поле 'folder' найдено:")
            print(json.dumps(product['folder'], indent=2, ensure_ascii=False))
        else:
            print("❌ Поле 'folder' НЕ найдено")
            print("Доступные ключи верхнего уровня:")
            for key in product.keys():
                print(f"  - {key}")

if __name__ == '__main__':
    main()