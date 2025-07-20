#!/usr/bin/env python
"""
Простая проверка остатков товара 376-41401 по всем складам
"""
import os
import sys
import django

# Настройка Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.sync.moysklad_client import MoySkladClient

def main():
    print("=== Проверка остатков товара 376-41401 по всем складам ===\n")
    
    client = MoySkladClient()
    
    # Получаем все склады
    try:
        warehouses = client.get_warehouses()
        print(f"Найдено складов: {len(warehouses)}")
        
        for warehouse in warehouses:
            if warehouse.get('archived'):
                print(f"⏸️  {warehouse['name']} - архивный, пропускаем")
                continue
            
            print(f"\n📦 Проверяем склад: {warehouse['name']} ({warehouse['id']})")
            
            try:
                # Получаем остатки по складу
                stock_data = client.get_stock_report(warehouse['id'], [])  # Без исключений
                
                # Ищем товар 376-41401
                found = False
                for item in stock_data:
                    if item.get('article') == '376-41401':
                        found = True
                        stock = item.get('stock', 0)
                        if stock > 0:
                            print(f"  ✅ НАЙДЕН! Остаток: {stock} шт.")
                        else:
                            print(f"  ⚠️  Найден, но остаток: {stock} шт.")
                        break
                
                if not found:
                    print(f"  ❌ Товар не найден на этом складе")
                    
            except Exception as e:
                print(f"  ❌ Ошибка получения остатков: {e}")
                
    except Exception as e:
        print(f"❌ Ошибка получения складов: {e}")
    
    print("\n=== Анализ последней синхронизации ===")
    try:
        from apps.sync.models import SyncLog
        last_sync = SyncLog.objects.order_by('-started_at').first()
        
        if last_sync:
            print(f"Последняя синхронизация: {last_sync.started_at}")
            print(f"Склад: {last_sync.warehouse_name}")
            print(f"Всего товаров в отчете по остаткам: {len(client.get_stock_report(last_sync.warehouse_id, []))}")
            print(f"Исключено групп: {len(last_sync.excluded_groups)}")
            print(f"Синхронизировано товаров: {last_sync.synced_products}")
            
            # Проверяем, есть ли товар среди остатков на этом складе
            target_warehouse_stock = client.get_stock_report(last_sync.warehouse_id, [])
            found_in_target = any(item.get('article') == '376-41401' for item in target_warehouse_stock)
            
            if found_in_target:
                print("✅ Товар ЕСТЬ в остатках целевого склада")
            else:
                print("❌ Товар ОТСУТСТВУЕТ в остатках целевого склада")
                print("🔍 Это основная причина, почему товар не синхронизируется!")
                
    except Exception as e:
        print(f"❌ Ошибка анализа синхронизации: {e}")

if __name__ == '__main__':
    main()