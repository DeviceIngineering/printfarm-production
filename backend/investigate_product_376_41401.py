#!/usr/bin/env python
"""
Скрипт для исследования проблемы синхронизации товара 376-41401
"""
import os
import sys
import django
import json
from datetime import datetime

# Настройка Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.sync.moysklad_client import MoySkladClient
from apps.sync.models import SyncLog
from apps.products.models import Product

def main():
    print("=== Исследование товара 376-41401 ===\n")
    
    # Исключенные группы из последней синхронизации
    excluded_groups = [
        'c9f548b0-4e34-11ee-0a80-0b2d000d38be',
        'cdfc5370-4a96-11f0-0a80-0e1a0048483b', 
        'f80eee84-4e2d-11ee-0a80-0dea000b0e6a',
        '6ae166ac-4e23-11ee-0a80-10c200088fdd',
        '821002ca-9221-11ef-0a80-16900019d6e0',
        '88a854b9-9c0f-11ee-0a80-018e00158d61',
        'd3f44dcb-7d92-11ee-0a80-064800000029',
        'd3f5010b-7d92-11ee-0a80-06480000002a'
    ]
    
    print(f"Исключенные группы из последней синхронизации ({len(excluded_groups)}):")
    for i, group_id in enumerate(excluded_groups, 1):
        print(f"  {i}. {group_id}")
    print()
    
    # Создаем клиент для МойСклад
    try:
        client = MoySkladClient()
        print("✅ МойСклад клиент создан успешно")
        
        # Тестируем соединение
        if client.test_connection():
            print("✅ Соединение с МойСклад работает")
        else:
            print("❌ Ошибка соединения с МойСклад")
            return
    except Exception as e:
        print(f"❌ Ошибка создания клиента: {e}")
        return
    
    print("\n=== 1. Получение списка групп товаров ===")
    try:
        groups = client.get_product_groups()
        print(f"✅ Получено {len(groups)} групп товаров")
        
        # Ищем группу "Подиумы"
        podiums_group = None
        for group in groups:
            if 'подиум' in group.get('name', '').lower():
                podiums_group = group
                break
        
        if podiums_group:
            print(f"✅ Найдена группа 'Подиумы':")
            print(f"  ID: {podiums_group['id']}")
            print(f"  Название: {podiums_group['name']}")
            print(f"  Полный путь: {podiums_group.get('pathName', 'Не указан')}")
            
            # Проверяем, исключена ли эта группа
            if podiums_group['id'] in excluded_groups:
                print(f"⚠️  ГРУППА ИСКЛЮЧЕНА ИЗ СИНХРОНИЗАЦИИ!")
                excluded_index = excluded_groups.index(podiums_group['id']) + 1
                print(f"  Находится в списке исключений под номером: {excluded_index}")
            else:
                print(f"✅ Группа НЕ исключена из синхронизации")
        else:
            print("❌ Группа 'Подиумы' не найдена")
            print("Доступные группы со словом 'подиум':")
            for group in groups:
                if 'подиум' in group.get('name', '').lower() or 'подиум' in group.get('pathName', '').lower():
                    print(f"  - {group['name']} (ID: {group['id']})")
    except Exception as e:
        print(f"❌ Ошибка получения групп: {e}")
    
    print("\n=== 2. Поиск товара 376-41401 через МойСклад API ===")
    try:
        # Попробуем найти товар через поиск по товарам
        search_params = {
            'filter': 'article=376-41401',
            'limit': 10
        }
        
        print("Поиск товара по артикулу 376-41401...")
        response = client._make_request('GET', 'entity/product', params=search_params)
        products = response.get('rows', [])
        
        if products:
            product = products[0]  # Берем первый найденный товар
            print(f"✅ Товар найден в МойСклад:")
            print(f"  ID: {product.get('id')}")
            print(f"  Название: {product.get('name')}")
            print(f"  Артикул: {product.get('article')}")
            
            # Проверяем группу товара
            folder = product.get('productFolder')
            if folder:
                folder_meta = folder.get('meta', {})
                folder_href = folder_meta.get('href', '')
                if folder_href:
                    folder_id = folder_href.split('/')[-1]
                    print(f"  Группа товара ID: {folder_id}")
                    
                    # Проверяем, исключена ли группа
                    if folder_id in excluded_groups:
                        print(f"  ⚠️  ГРУППА ТОВАРА ИСКЛЮЧЕНА ИЗ СИНХРОНИЗАЦИИ!")
                        excluded_index = excluded_groups.index(folder_id) + 1
                        print(f"  Позиция в списке исключений: {excluded_index}")
                    else:
                        print(f"  ✅ Группа товара НЕ исключена")
                        
                    # Получаем информацию о группе
                    try:
                        folder_response = client._make_request('GET', f'entity/productfolder/{folder_id}')
                        print(f"  Название группы: {folder_response.get('name')}")
                        print(f"  Полный путь группы: {folder_response.get('pathName')}")
                    except Exception as e:
                        print(f"  ❌ Ошибка получения информации о группе: {e}")
            else:
                print("  ⚠️  У товара не указана группа")
        else:
            print("❌ Товар с артикулом 376-41401 не найден в МойСклад")
    except Exception as e:
        print(f"❌ Ошибка поиска товара: {e}")
    
    print("\n=== 3. Проверка товара в локальной базе данных ===")
    try:
        local_product = Product.objects.filter(article='376-41401').first()
        if local_product:
            print(f"✅ Товар найден в локальной БД:")
            print(f"  ID: {local_product.id}")
            print(f"  МойСклад ID: {local_product.moysklad_id}")
            print(f"  Название: {local_product.name}")
            print(f"  Группа: {local_product.product_group_name}")
            print(f"  Группа ID: {local_product.product_group_id}")
            print(f"  Дата последней синхронизации: {local_product.last_synced_at}")
            print(f"  Остаток: {local_product.current_stock}")
            print(f"  Изображений: {local_product.images.count()}")
        else:
            print("❌ Товар не найден в локальной БД")
    except Exception as e:
        print(f"❌ Ошибка проверки локальной БД: {e}")
    
    print("\n=== 4. Анализ последних синхронизаций ===")
    try:
        recent_syncs = SyncLog.objects.order_by('-started_at')[:5]
        print(f"Последние {len(recent_syncs)} синхронизаций:")
        
        for i, sync_log in enumerate(recent_syncs, 1):
            print(f"\n  {i}. Синхронизация от {sync_log.started_at}")
            print(f"     Статус: {sync_log.status}")
            print(f"     Склад: {sync_log.warehouse_name} ({sync_log.warehouse_id})")
            print(f"     Исключенных групп: {len(sync_log.excluded_groups)}")
            print(f"     Всего товаров: {sync_log.total_products}")
            print(f"     Синхронизировано: {sync_log.synced_products}")
            print(f"     Ошибок: {sync_log.failed_products}")
            
            if sync_log.error_details:
                print(f"     Ошибки: {sync_log.error_details[:200]}...")
    except Exception as e:
        print(f"❌ Ошибка анализа синхронизаций: {e}")
    
    print("\n=== 5. Тестовый запрос остатков по складу ===")
    try:
        from django.conf import settings
        warehouse_id = settings.MOYSKLAD_CONFIG['default_warehouse_id']
        
        print(f"Получение остатков по складу {warehouse_id}...")
        stock_data = client.get_stock_report(warehouse_id, excluded_groups)
        
        print(f"✅ Получено {len(stock_data)} товаров с остатками")
        
        # Ищем наш товар в остатках
        found_in_stock = False
        for item in stock_data:
            if item.get('article') == '376-41401':
                found_in_stock = True
                print(f"✅ Товар 376-41401 найден в остатках:")
                print(f"  Остаток: {item.get('stock', 0)}")
                print(f"  Название: {item.get('name', 'Не указано')}")
                break
        
        if not found_in_stock:
            print("❌ Товар 376-41401 НЕ найден в остатках")
            print("Возможные причины:")
            print("  1. Товар исключен из-за группы")
            print("  2. У товара нулевой остаток на складе")
            print("  3. Товар не привязан к указанному складу")
    except Exception as e:
        print(f"❌ Ошибка получения остатков: {e}")

    print("\n=== ЗАКЛЮЧЕНИЕ ===")
    print("Для решения проблемы проверьте:")
    print("1. Принадлежит ли товар к исключенной группе")
    print("2. Есть ли остатки товара на выбранном складе") 
    print("3. Корректно ли указан ID склада в настройках")
    print("4. Нет ли ошибок в логах синхронизации")

if __name__ == '__main__':
    main()