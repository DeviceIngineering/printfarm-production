#!/usr/bin/env python
"""
Повторная синхронизация группы "Подиумы" с исправленным кодом
"""
import os
import sys
import django

# Настройка Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.sync.services import SyncService

def main():
    print("=== Повторная синхронизация группы 'Подиумы' ===\n")
    
    # Запускаем синхронизацию только группы Подиумы
    sync_service = SyncService()
    
    # Получаем ID всех групп кроме Подиумы для исключения
    groups = sync_service.client.get_product_groups()
    podiums_group = next(g for g in groups if g['name'] == 'Подиумы')
    excluded_groups = [g['id'] for g in groups if g['id'] != podiums_group['id']]
    
    warehouse_id = '241ed919-a631-11ee-0a80-07a9000bb947'
    
    print(f"Синхронизируем только группу: {podiums_group['name']}")
    print(f"Исключаем {len(excluded_groups)} групп")
    
    sync_log = sync_service.sync_products(
        warehouse_id=warehouse_id,
        excluded_groups=excluded_groups,
        sync_type='manual',
        sync_images=False
    )
    
    print(f"\nРезультат синхронизации: {sync_log.status}")
    print(f"Синхронизировано товаров: {sync_log.synced_products}")
    
    if sync_log.status == 'success':
        print("\n✅ Синхронизация успешна! Проверяем остатки...")
        
        from apps.products.models import Product
        
        podiums_products = Product.objects.filter(product_group_name__icontains='Подиумы').order_by('article')
        
        print(f"\nТовары группы 'Подиумы' ({podiums_products.count()} шт.):")
        for product in podiums_products:
            stock_color = "✅" if product.current_stock > 0 else "📦"
            print(f"  {stock_color} {product.article}: {product.current_stock} шт. - {product.name[:50]}...")
            
        # Проверяем конкретно товар 320-42802
        target_product = podiums_products.filter(article='320-42802').first()
        if target_product:
            print(f"\n🎯 Товар 320-42802:")
            print(f"   Остаток: {target_product.current_stock}")
            print(f"   Последняя синхронизация: {target_product.last_synced_at}")
        
    else:
        print(f"❌ Синхронизация завершилась с ошибкой: {sync_log.error_details}")

if __name__ == '__main__':
    main()