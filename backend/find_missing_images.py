#!/usr/bin/env python3
"""
Find products that should have images but don't have them loaded.
"""
import os
import sys
import django

# Setup Django
sys.path.append('/Users/dim11/Documents/myProjects/Factory_v2/backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()

from apps.products.models import Product
from apps.sync.moysklad_client import MoySkladClient

def find_missing_images():
    """Find products that have images in МойСклад but not in DB."""
    
    print("🔍 ПОИСК ТОВАРОВ С ПРОПУЩЕННЫМИ ИЗОБРАЖЕНИЯМИ")
    print("=" * 50)
    
    client = MoySkladClient()
    
    # Возьмем случайную выборку товаров без изображений
    products_without_images = Product.objects.filter(
        images__isnull=True,
        last_synced_at__isnull=False
    ).distinct()[:50]  # Проверим первые 50
    
    print(f"Проверяем {len(products_without_images)} товаров без изображений...")
    
    missing_images = []
    checked = 0
    
    for product in products_without_images:
        checked += 1
        if checked % 10 == 0:
            print(f"Проверено {checked}/{len(products_without_images)} товаров...")
        
        try:
            # Проверяем изображения в МойСклад
            images_data = client.get_product_images(product.moysklad_id)
            
            if images_data:  # Есть изображения в МойСклад
                missing_images.append({
                    'product': product,
                    'images_count': len(images_data),
                    'images_data': images_data
                })
                
        except Exception as e:
            print(f"❌ Ошибка для товара {product.article}: {str(e)}")
            continue
    
    print(f"\n📊 РЕЗУЛЬТАТЫ:")
    print(f"Проверено товаров: {checked}")
    print(f"Товаров с пропущенными изображениями: {len(missing_images)}")
    
    if missing_images:
        print(f"\n🖼️ ТОВАРЫ С ПРОПУЩЕННЫМИ ИЗОБРАЖЕНИЯМИ:")
        for i, item in enumerate(missing_images[:10], 1):  # Показываем первые 10
            product = item['product']
            print(f"{i:2d}. {product.article}: {product.name[:50]}...")
            print(f"    Изображений в МойСклад: {item['images_count']}")
            
            # Попробуем загрузить изображения
            try:
                from apps.sync.services import SyncService
                sync_service = SyncService()
                synced_count = sync_service.sync_product_images(product)
                print(f"    ✅ Загружено: {synced_count} изображений")
            except Exception as e:
                print(f"    ❌ Ошибка загрузки: {str(e)}")
    
    print(f"\n🎯 РЕКОМЕНДАЦИИ:")
    if len(missing_images) > 20:
        print("1. Увеличить лимит синхронизации изображений с 20 до 50-100 товаров")
        print("2. Добавить фоновую задачу для периодической загрузки оставшихся изображений")
        print("3. Создать API endpoint для ручной загрузки изображений")
    elif missing_images:
        print("1. Запустить дополнительную синхронизацию изображений")
        print("2. Проверить логи на ошибки загрузки")
    else:
        print("✅ Все товары без изображений в БД действительно не имеют изображений в МойСклад")

if __name__ == '__main__':
    find_missing_images()