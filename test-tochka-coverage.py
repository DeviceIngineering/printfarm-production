#!/usr/bin/env python3
"""
Тестирование анализа покрытия товаров в Точке
Логика: Excel содержит товары которые ЕСТЬ в Точке,
нужно найти товары МойСклад которых НЕТ в Точке
"""

import requests
import json
import pandas as pd

def test_tochka_coverage():
    print("🔍 Тестирование анализа покрытия товаров в Точке")
    
    # 1. Получаем список товаров на производство из МойСклад
    print("\n1️⃣ Получаем товары на производство из МойСклад...")
    
    try:
        response = requests.get('http://localhost:8000/api/v1/tochka/production/')
        if response.ok:
            production_data = response.json()
            production_products = production_data.get('results', [])
            print(f"✅ Найдено {len(production_products)} товаров к производству")
            
            if len(production_products) > 0:
                print("📋 Примеры товаров к производству:")
                for i, product in enumerate(production_products[:5]):
                    print(f"   {product['article']} - {product['name']} (к производству: {product['production_needed']} шт)")
            
        else:
            print("❌ Ошибка загрузки товаров на производство")
            return
            
    except Exception as e:
        print(f"❌ Ошибка подключения: {e}")
        return
    
    # 2. Создаем тестовые данные Excel (товары которые ЕСТЬ в Точке)
    print("\n2️⃣ Создаем тестовые данные Excel (товары Точки)...")
    
    # Берем часть товаров из производства (симулируем что они есть в Точке)
    # и добавляем несколько других артикулов
    excel_test_data = []
    
    # Берем первые 3 товара из производства (они ЕСТЬ в Точке)
    for i, product in enumerate(production_products[:3]):
        excel_test_data.append({
            'article': product['article'],
            'orders': (i + 1) * 20,  # Симулируем заказы
            'row_number': i + 1,
            'has_duplicates': False,
            'duplicate_rows': None
        })
    
    # Добавляем артикул которого нет в производстве (но есть в Точке)
    excel_test_data.append({
        'article': 'TOCHKA-ONLY-001',
        'orders': 50,
        'row_number': 4,
        'has_duplicates': False,
        'duplicate_rows': None
    })
    
    print(f"📋 Товары в Excel (Точка): {len(excel_test_data)} шт")
    for item in excel_test_data:
        print(f"   {item['article']} -> {item['orders']} заказов")
    
    print(f"\n❗ Товары МойСклад которых НЕТ в Excel (Точке):")
    missing_in_tochka = []
    for product in production_products[3:8]:  # Берем товары 4-8 как отсутствующие
        print(f"   {product['article']} - {product['name']}")
        missing_in_tochka.append(product['article'])
    
    # 3. Тестируем API анализа
    print("\n3️⃣ Тестируем API анализа покрытия...")
    
    try:
        merge_response = requests.post(
            'http://localhost:8000/api/v1/tochka/merge-with-products/',
            json={'excel_data': excel_test_data},
            headers={'Content-Type': 'application/json'}
        )
        
        if merge_response.ok:
            merge_data = merge_response.json()
            print(f"✅ {merge_data['message']}")
            
            print(f"\n📊 Статистика анализа:")
            print(f"   Всего товаров к производству: {merge_data['total_production_needed']}")
            print(f"   Есть в Точке: {merge_data['products_in_tochka']}")
            print(f"   НЕТ в Точке: {merge_data['products_not_in_tochka']} ⚠️")
            print(f"   Процент покрытия: {merge_data['coverage_rate']}%")
            
            print(f"\n🔍 Детальные результаты:")
            # Сначала товары которых НЕТ в Точке
            not_in_tochka = [item for item in merge_data['data'] if item['needs_registration']]
            if not_in_tochka:
                print("\n❌ ТОВАРЫ КОТОРЫХ НЕТ В ТОЧКЕ (требуют регистрации):")
                for item in not_in_tochka[:10]:  # Первые 10
                    print(f"   {item['article']} - {item['product_name']}")
                    print(f"      └─ К производству: {item['production_needed']} шт")
                    print(f"      └─ Приоритет: {item['production_priority']}")
                    print()
            
            # Потом товары которые ЕСТЬ в Точке
            in_tochka = [item for item in merge_data['data'] if item['is_in_tochka']]
            if in_tochka:
                print("\n✅ ТОВАРЫ КОТОРЫЕ ЕСТЬ В ТОЧКЕ:")
                for item in in_tochka[:5]:  # Первые 5
                    print(f"   {item['article']} - {item['product_name']}")
                    print(f"      └─ Заказов в Точке: {item['orders_in_tochka']} шт")
                    print(f"      └─ К производству: {item['production_needed']} шт")
                    print()
            
        else:
            error_data = merge_response.json()
            print(f"❌ Ошибка API: {error_data.get('error', 'Неизвестная ошибка')}")
            
    except Exception as e:
        print(f"❌ Ошибка тестирования: {e}")

def create_test_excel_for_tochka():
    """Создает Excel файл симулирующий данные из Точки"""
    print("\n4️⃣ Создаем Excel файл с товарами Точки...")
    
    try:
        # Получаем товары из производства
        response = requests.get('http://localhost:8000/api/v1/tochka/production/')
        if response.ok:
            production_data = response.json()
            products = production_data.get('results', [])
            
            if len(products) >= 5:
                # Создаем Excel с ЧАСТЬЮ товаров (симулируем что не все есть в Точке)
                excel_data = []
                
                # Берем каждый второй товар (50% покрытие)
                for i in range(0, min(10, len(products)), 2):
                    product = products[i]
                    excel_data.append({
                        'Артикул товара': product['article'],
                        'Заказов, шт.': (i + 1) * 15
                    })
                
                # Добавляем дубликат
                if len(excel_data) > 0:
                    excel_data.append({
                        'Артикул товара': excel_data[0]['Артикул товара'],
                        'Заказов, шт.': 30
                    })
                
                # Сохраняем в Excel
                df = pd.DataFrame(excel_data)
                filename = 'test-tochka-products.xlsx'
                df.to_excel(filename, index=False)
                
                print(f"✅ Создан файл: {filename}")
                print("📋 Содержимое файла (товары Точки):")
                for item in excel_data:
                    print(f"   {item['Артикул товара']} -> {item['Заказов, шт.']} шт")
                
                print(f"\n💡 При загрузке этого файла:")
                print(f"   - {len(excel_data)-1} уникальных товаров будут помечены как 'Есть в Точке'")
                print(f"   - Остальные товары МойСклад будут помечены как 'НЕТ в Точке'")
                print(f"   - Ожидаемое покрытие: ~50%")
                
            else:
                print("❌ Недостаточно товаров в производстве для создания тестового файла")
                
    except Exception as e:
        print(f"❌ Ошибка создания Excel файла: {e}")

if __name__ == "__main__":
    test_tochka_coverage()
    create_test_excel_for_tochka()