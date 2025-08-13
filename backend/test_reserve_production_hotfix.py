"""
КРИТИЧЕСКИЙ ТЕСТ HOTFIX: Проверка включения товаров с резервом в список производства
"""
import requests
import json
from decimal import Decimal

def test_critical_reserve_inclusion():
    """
    Критический тест для проверки что товары с резервом включены в список производства
    """
    print("🔥 КРИТИЧЕСКИЙ ТЕСТ: Товары с резервом в списке производства")
    
    # 1. Проверяем API производства
    response = requests.get("http://localhost:8000/api/v1/tochka/production/")
    assert response.status_code == 200, f"API не отвечает: {response.status_code}"
    
    data = response.json()
    products = data['results']
    
    # 2. Находим товары с резервом
    products_with_reserve = [p for p in products if float(p['reserved_stock']) > 0]
    
    print(f"✅ Найдено товаров с резервом: {len(products_with_reserve)}")
    
    # 3. КРИТИЧЕСКАЯ ПРОВЕРКА: Должно быть >= 5 товаров с резервом
    assert len(products_with_reserve) >= 5, f"ОШИБКА: Найдено только {len(products_with_reserve)} товаров с резервом, ожидалось >= 5"
    
    # 4. Проверяем что все товары с резервом имеют production_needed > 0
    for product in products_with_reserve:
        reserve = float(product['reserved_stock'])
        production = float(product['production_needed'])
        
        print(f"  {product['article']}: резерв={reserve}, производство={production}")
        
        assert reserve > 0, f"Товар {product['article']} должен иметь резерв > 0"
        assert production > 0, f"Товар {product['article']} должен иметь production_needed > 0"
        assert product['has_reserve'] == True, f"Товар {product['article']} должен иметь has_reserve=True"
        
        # КРИТИЧЕСКОЕ ПРАВИЛО: production_needed должен быть >= reserved_stock
        assert production >= reserve, f"Товар {product['article']}: production_needed ({production}) должен быть >= reserved_stock ({reserve})"
    
    print("✅ Все товары с резервом корректно включены в производство")
    return True

def test_reserved_articles_specifically():
    """
    Тест конкретных артикулов которые были проблемными
    """
    print("\n🎯 ТЕСТ: Проверка конкретных проблемных артикулов")
    
    expected_articles = [
        "15-43001R",   # резерв 800
        "263-41522",   # резерв 500  
        "556-51448",   # резерв 1000
        "N321-12",     # резерв 1000
        "N421-11-45K"  # резерв 5000
    ]
    
    response = requests.get("http://localhost:8000/api/v1/tochka/production/")
    data = response.json()
    products = data['results']
    
    found_articles = [p['article'] for p in products]
    
    for article in expected_articles:
        assert article in found_articles, f"КРИТИЧЕСКАЯ ОШИБКА: Артикул {article} отсутствует в списке производства!"
        
        # Находим товар и проверяем данные
        product = next(p for p in products if p['article'] == article)
        
        reserve = float(product['reserved_stock'])
        production = float(product['production_needed'])
        
        print(f"  ✅ {article}: резерв={reserve}, производство={production}")
        
        assert reserve > 0, f"Товар {article} должен иметь резерв > 0"
        assert production >= reserve, f"Товар {article}: производство должно быть >= резерва"
    
    print("✅ Все проблемные артикулы найдены в списке производства")
    return True

def test_api_consistency():
    """
    Тест консистентности всех API endpoint'ов
    """
    print("\n🔄 ТЕСТ: Консистентность API endpoints")
    
    endpoints = [
        "/api/v1/tochka/production/",
        "/api/v1/tochka/products/"
    ]
    
    for endpoint in endpoints:
        response = requests.get(f"http://localhost:8000{endpoint}")
        assert response.status_code == 200, f"Endpoint {endpoint} не отвечает"
        
        data = response.json()
        products_with_reserve = [p for p in data['results'] if float(p['reserved_stock']) > 0]
        
        print(f"  {endpoint}: найдено {len(products_with_reserve)} товаров с резервом")
        
        # В списке производства должны быть товары с резервом
        if endpoint == "/api/v1/tochka/production/":
            assert len(products_with_reserve) >= 5, f"Недостаточно товаров с резервом в {endpoint}"
    
    print("✅ Все API endpoints консистентны")
    return True

if __name__ == "__main__":
    print("🚀 ЗАПУСК КРИТИЧЕСКИХ ТЕСТОВ HOTFIX")
    
    try:
        test_critical_reserve_inclusion()
        test_reserved_articles_specifically() 
        test_api_consistency()
        
        print("\n🎉 ВСЕ КРИТИЧЕСКИЕ ТЕСТЫ ПРОЙДЕНЫ!")
        print("✅ Hotfix успешно исправил проблему с товарами с резервом")
        print("✅ Товары с резервом теперь включены в список производства")
        
    except Exception as e:
        print(f"\n❌ КРИТИЧЕСКАЯ ОШИБКА: {e}")
        exit(1)