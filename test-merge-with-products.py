#!/usr/bin/env python3
"""
Тестирование объединения Excel данных с товарами из базы данных
"""

import requests
import json
import pandas as pd

def test_merge_api():
    print("🔧 Тестирование API объединения Excel данных с товарами")
    
    # Сначала получаем список товаров из базы
    print("\n1️⃣ Получаем товары из базы данных...")
    
    try:
        response = requests.get('http://localhost:8000/api/v1/tochka/products/')
        if response.ok:
            products_data = response.json()
            products = products_data.get('results', [])
            print(f"✅ Загружено {len(products)} товаров из базы")
            
            # Берем первые 5 артикулов для теста
            test_articles = [product['article'] for product in products[:5] if product.get('article')]
            print(f"🎯 Тестовые артикулы: {test_articles}")
            
        else:
            print("❌ Ошибка загрузки товаров из базы")
            return
            
    except Exception as e:
        print(f"❌ Ошибка подключения: {e}")
        return
    
    # Создаем тестовые Excel данные с существующими и несуществующими артикулами
    print("\n2️⃣ Создаем тестовые Excel данные...")
    
    excel_test_data = []
    
    # Добавляем существующие артикулы
    for i, article in enumerate(test_articles):
        excel_test_data.append({
            'article': article,
            'orders': (i + 1) * 10,
            'row_number': i + 1,
            'has_duplicates': False,
            'duplicate_rows': None
        })
    
    # Добавляем несуществующий артикул
    excel_test_data.append({
        'article': 'TEST-999-FAKE',
        'orders': 50,
        'row_number': len(test_articles) + 1,
        'has_duplicates': False,
        'duplicate_rows': None
    })
    
    # Добавляем дубликат первого артикула (суммирование)
    if test_articles:
        excel_test_data.append({
            'article': test_articles[0],
            'orders': 25,
            'row_number': len(test_articles) + 2,
            'has_duplicates': True,
            'duplicate_rows': [len(test_articles) + 2]
        })
        # Обновляем первую запись как имеющую дубликаты
        excel_test_data[0]['has_duplicates'] = True
        excel_test_data[0]['duplicate_rows'] = [len(test_articles) + 2]
        excel_test_data[0]['orders'] = excel_test_data[0]['orders'] + 25  # 10 + 25 = 35
    
    print(f"📋 Подготовлено {len(excel_test_data)} записей Excel:")
    for item in excel_test_data:
        dup_info = f" (дубликат: +{item['duplicate_rows']})" if item['has_duplicates'] else ""
        print(f"   {item['article']} -> {item['orders']} шт{dup_info}")
    
    # Тестируем API объединения
    print("\n3️⃣ Тестируем API объединения...")
    
    try:
        merge_response = requests.post(
            'http://localhost:8000/api/v1/tochka/merge-with-products/',
            json={'excel_data': excel_test_data},
            headers={'Content-Type': 'application/json'}
        )
        
        if merge_response.ok:
            merge_data = merge_response.json()
            print(f"✅ {merge_data['message']}")
            
            print(f"\n📊 Статистика объединения:")
            print(f"   Всего записей: {merge_data['total_records']}")
            print(f"   Найдено товаров: {merge_data['matched_products']}")
            print(f"   Не найдено: {merge_data['unmatched_products']}")
            print(f"   Процент совпадений: {merge_data['match_rate']}%")
            
            print(f"\n🔍 Детальные результаты:")
            for item in merge_data['data']:
                match_status = "✅ НАЙДЕН" if item['product_matched'] else "❌ НЕ НАЙДЕН"
                product_name = item.get('product_name', 'N/A')
                stock = item.get('current_stock', 'N/A')
                production = item.get('production_needed', 'N/A')
                
                print(f"   {item['article']}: {item['orders']} заказов | {match_status}")
                if item['product_matched']:
                    print(f"      └─ Товар: {product_name}")
                    print(f"      └─ Остаток: {stock} шт, К производству: {production} шт")
                print()
            
        else:
            error_data = merge_response.json()
            print(f"❌ Ошибка API: {error_data.get('error', 'Неизвестная ошибка')}")
            
    except Exception as e:
        print(f"❌ Ошибка тестирования: {e}")

def create_test_excel_with_real_articles():
    """Создает Excel файл с реальными артикулами из базы"""
    print("\n4️⃣ Создаем Excel файл с реальными артикулами...")
    
    try:
        # Получаем товары из базы
        response = requests.get('http://localhost:8000/api/v1/tochka/products/')
        if response.ok:
            products_data = response.json()
            products = products_data.get('results', [])
            
            if len(products) >= 3:
                # Создаем Excel с реальными артикулами
                excel_data = []
                
                # Берем первые 3 товара
                for i, product in enumerate(products[:3]):
                    excel_data.append({
                        'Артикул товара': product['article'],
                        'Заказов, шт.': (i + 1) * 15
                    })
                
                # Добавляем дубликат первого товара
                excel_data.append({
                    'Артикул товара': products[0]['article'],
                    'Заказов, шт.': 30
                })
                
                # Добавляем несуществующий артикул
                excel_data.append({
                    'Артикул товара': 'FAKE-ARTICLE-999',
                    'Заказов, шт.': 100
                })
                
                # Сохраняем в Excel
                df = pd.DataFrame(excel_data)
                filename = 'test-merge-with-real-articles.xlsx'
                df.to_excel(filename, index=False)
                
                print(f"✅ Создан файл: {filename}")
                print("📋 Содержимое файла:")
                for item in excel_data:
                    print(f"   {item['Артикул товара']} -> {item['Заказов, шт.']} шт")
                
                print(f"\n💡 Ожидаемые результаты:")
                print(f"   {products[0]['article']}: 15 + 30 = 45 шт (найден в базе)")
                print(f"   {products[1]['article']}: 30 шт (найден в базе)")
                print(f"   {products[2]['article']}: 45 шт (найден в базе)")
                print(f"   FAKE-ARTICLE-999: 100 шт (НЕ найден в базе)")
                
            else:
                print("❌ Недостаточно товаров в базе для создания тестового файла")
                
    except Exception as e:
        print(f"❌ Ошибка создания Excel файла: {e}")

if __name__ == "__main__":
    test_merge_api()
    create_test_excel_with_real_articles()