#!/usr/bin/env python
"""
Проверка актуальных остатков товаров группы "Подиумы"
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
    print("=== Сравнение остатков товаров группы 'Подиумы' ===\n")
    
    client = MoySkladClient()
    
    try:
        # Получаем остатки из МойСклад
        print("1. Получаем актуальные остатки из МойСклад...")
        warehouse_id = '241ed919-a631-11ee-0a80-07a9000bb947'
        groups = client.get_product_groups()
        podiums_group = next(g for g in groups if g['name'] == 'Подиумы')
        excluded_groups = [g['id'] for g in groups if g['id'] != podiums_group['id']]
        
        products = client.get_all_products_with_stock(warehouse_id, excluded_groups)
        
        print(f"✅ Получено {len(products)} товаров из МойСклад")
        
        # Получаем остатки из локальной БД
        print("\n2. Получаем остатки из локальной БД...")
        local_products = Product.objects.filter(product_group_name__icontains='Подиумы')
        local_dict = {p.article: p for p in local_products}
        
        print(f"✅ Получено {local_products.count()} товаров из локальной БД")
        
        # Сравниваем остатки
        print("\n3. Сравнение остатков:")
        print("Артикул\t\tМойСклад\tЛокальная БД\tРазность")
        print("-" * 60)
        
        discrepancies = []
        
        for product in products:
            article = product.get('article', '')
            moysklad_stock = product.get('stock', 0)
            name = product.get('name', '')[:30]
            
            local_product = local_dict.get(article)
            local_stock = float(local_product.current_stock) if local_product else 0
            
            difference = moysklad_stock - local_stock
            
            if difference != 0:
                discrepancies.append({
                    'article': article,
                    'name': name,
                    'moysklad': moysklad_stock,
                    'local': local_stock,
                    'diff': difference
                })
            
            print(f"{article:<12}\t{moysklad_stock:<8}\t{local_stock:<12}\t{difference:+.1f}")
        
        print("\n4. Анализ расхождений:")
        if discrepancies:
            print(f"❌ Найдено {len(discrepancies)} товаров с расхождениями:")
            for item in discrepancies:
                print(f"  📦 {item['article']}: МС={item['moysklad']}, БД={item['local']} (разность: {item['diff']:+.1f})")
                print(f"     {item['name']}...")
        else:
            print("✅ Все остатки синхронизированы корректно")
        
        # Проверяем товар 320-42802 отдельно
        print("\n5. Детальная проверка товара 320-42802:")
        target_article = '320-42802'
        
        moysklad_product = next((p for p in products if p.get('article') == target_article), None)
        local_product = local_dict.get(target_article)
        
        if moysklad_product:
            print(f"✅ МойСклад: остаток = {moysklad_product.get('stock', 0)} шт.")
        else:
            print("❌ Товар не найден в МойСклад")
        
        if local_product:
            print(f"✅ Локальная БД: остаток = {local_product.current_stock} шт.")
            print(f"   Последняя синхронизация: {local_product.last_synced_at}")
        else:
            print("❌ Товар не найден в локальной БД")
        
        # Проверяем последнюю синхронизацию
        print("\n6. Информация о последней синхронизации:")
        from apps.sync.models import SyncLog
        last_sync = SyncLog.objects.order_by('-started_at').first()
        
        if last_sync:
            print(f"Дата: {last_sync.started_at}")
            print(f"Статус: {last_sync.status}")
            print(f"Склад: {last_sync.warehouse_name}")
            print(f"Синхронизировано товаров: {last_sync.synced_products}")
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()