#!/usr/bin/env python3
"""
Скрипт для исправления некорректно сохраненных данных цвета в БД
"""
import os
import sys
import django
import json
import re

# Добавляем путь к проекту Django
sys.path.append('/Users/dim11/Documents/myProjects/Factory_v3/backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()

from apps.products.models import Product

def fix_color_data():
    """
    Исправляет некорректно сохраненные данные цвета в виде JSON строк
    """
    print("🔍 Поиск товаров с некорректными данными цвета...")
    
    # Находим товары с цветом, содержащим JSON структуру
    products_with_json_color = Product.objects.filter(
        color__icontains='{"meta":'
    ).exclude(color='')
    
    fixed_count = 0
    total_count = products_with_json_color.count()
    
    print(f"📊 Найдено товаров с некорректным цветом: {total_count}")
    
    for product in products_with_json_color:
        try:
            print(f"🔧 Исправляем товар {product.article}: {product.color[:50]}...")
            
            # Пытаемся распарсить JSON
            if product.color.startswith('{') and '"name"' in product.color:
                try:
                    color_data = json.loads(product.color)
                    if isinstance(color_data, dict) and 'name' in color_data:
                        new_color = color_data['name']
                        print(f"   ✅ Извлечен цвет: {new_color}")
                        product.color = new_color
                        product.save()
                        fixed_count += 1
                        continue
                except json.JSONDecodeError:
                    pass
            
            # Попытка извлечь через регулярное выражение
            name_match = re.search(r'"name":\s*"([^"]+)"', product.color)
            if name_match:
                new_color = name_match.group(1)
                print(f"   ✅ Извлечен цвет (regex): {new_color}")
                product.color = new_color
                product.save()
                fixed_count += 1
            else:
                print(f"   ❌ Не удалось извлечь цвет, очищаем поле")
                product.color = ''
                product.save()
                
        except Exception as e:
            print(f"   ❌ Ошибка при обработке товара {product.article}: {e}")
            # В случае ошибки очищаем поле
            product.color = ''
            product.save()
    
    print(f"✅ Исправлено товаров: {fixed_count} из {total_count}")
    return fixed_count, total_count

if __name__ == '__main__':
    fix_color_data()