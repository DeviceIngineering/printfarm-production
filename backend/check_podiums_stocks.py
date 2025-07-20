#!/usr/bin/env python
"""
Скрипт для проверки остатков товаров группы "Подиумы"
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
    print("=== Проверка товаров группы 'Подиумы' ===\n")
    
    client = MoySkladClient()
    
    try:
        print("1. Получаем группы товаров из МойСклад...")
        groups = client.get_product_groups()
        
        # Ищем группу "Подиумы"
        podiums_group = None
        for group in groups:
            if group['name'] == 'Подиумы':
                podiums_group = group
                break
        
        if not podiums_group:
            print("❌ Группа 'Подиумы' не найдена в МойСклад")
            print("Доступные группы:")
            for group in groups[:10]:
                print(f"  - {group['name']} ({group['id']})")
            return
        
        print(f"✅ Найдена группа 'Подиумы': {podiums_group['id']}")
        
        print("\n2. Получаем товары группы 'Подиумы' из МойСклад...")
        
        # Получаем все товары с остатками, исключив все группы кроме "Подиумы"
        all_groups = [g['id'] for g in groups]
        excluded_groups = [g['id'] for g in groups if g['id'] != podiums_group['id']]
        
        warehouse_id = '241ed919-a631-11ee-0a80-07a9000bb947'  # Адресный склад
        
        podiums_products = client.get_all_products_with_stock(warehouse_id, excluded_groups)
        
        print(f"✅ Найдено {len(podiums_products)} товаров в группе 'Подиумы' на складе")
        
        print("\n3. Анализ остатков в МойСклад:")
        zero_stock_count = 0
        positive_stock_count = 0
        
        for product in podiums_products:
            stock = product.get('stock', 0)
            article = product.get('article', 'Без артикула')
            name = product.get('name', 'Без названия')[:50]
            
            if stock == 0:
                zero_stock_count += 1
                print(f"  📦 {article}: {name}... - ОСТАТОК: {stock}")
            else:
                positive_stock_count += 1
                print(f"  ✅ {article}: {name}... - ОСТАТОК: {stock}")
        
        print(f"\n📊 Статистика МойСклад:")
        print(f"  - Товаров с нулевыми остатками: {zero_stock_count}")
        print(f"  - Товаров с положительными остатками: {positive_stock_count}")
        print(f"  - Всего товаров: {len(podiums_products)}")
        
        print("\n4. Проверяем товары в локальной БД...")
        
        # Получаем товары группы "Подиумы" из локальной БД
        local_podiums = Product.objects.filter(product_group_name__icontains='Подиумы')
        
        print(f"✅ В локальной БД найдено {local_podiums.count()} товаров группы 'Подиумы'")
        
        if local_podiums.exists():
            print("\n📊 Статистика локальной БД:")
            local_zero_stock = local_podiums.filter(current_stock=0).count()
            local_positive_stock = local_podiums.filter(current_stock__gt=0).count()
            
            print(f"  - Товаров с нулевыми остатками: {local_zero_stock}")
            print(f"  - Товаров с положительными остатками: {local_positive_stock}")
            
            print("\n📝 Товары в локальной БД:")
            for product in local_podiums.order_by('article'):
                print(f"  📦 {product.article}: {product.name[:50]}... - ОСТАТОК: {product.current_stock}")
        else:
            print("❌ В локальной БД нет товаров группы 'Подиумы'")
        
        print("\n5. Сравнение данных:")
        
        # Сравниваем артикулы из МойСклад и локальной БД
        moysklad_articles = {p.get('article') for p in podiums_products if p.get('article')}
        local_articles = set(local_podiums.values_list('article', flat=True))
        
        missing_in_local = moysklad_articles - local_articles
        extra_in_local = local_articles - moysklad_articles
        
        if missing_in_local:
            print(f"❌ Товары из МойСклад, отсутствующие в локальной БД ({len(missing_in_local)}):")
            for article in sorted(missing_in_local):
                print(f"  - {article}")
        
        if extra_in_local:
            print(f"⚠️  Товары в локальной БД, отсутствующие в МойСклад ({len(extra_in_local)}):")
            for article in sorted(extra_in_local):
                print(f"  - {article}")
        
        if not missing_in_local and not extra_in_local:
            print("✅ Все товары синхронизированы корректно!")
        
        print("\n=== Проверка товара 376-41401 ===")
        
        # Специальная проверка товара 376-41401
        target_article = '376-41401'
        
        # В МойСклад
        moysklad_target = None
        for product in podiums_products:
            if product.get('article') == target_article:
                moysklad_target = product
                break
        
        if moysklad_target:
            print(f"✅ Товар {target_article} найден в МойСклад:")
            print(f"  - Название: {moysklad_target.get('name', 'Неизвестно')}")
            print(f"  - Остаток: {moysklad_target.get('stock', 0)}")
        else:
            print(f"❌ Товар {target_article} НЕ найден в МойСклад среди товаров группы 'Подиумы'")
        
        # В локальной БД
        local_target = local_podiums.filter(article=target_article).first()
        
        if local_target:
            print(f"✅ Товар {target_article} найден в локальной БД:")
            print(f"  - Название: {local_target.name}")
            print(f"  - Остаток: {local_target.current_stock}")
            print(f"  - Последняя синхронизация: {local_target.last_synced_at}")
        else:
            print(f"❌ Товар {target_article} НЕ найден в локальной БД")
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()