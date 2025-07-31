#!/usr/bin/env python3
"""
Тестовый скрипт для проверки соединения с МойСклад API
"""
import os
import sys
import django

# Настраиваем Django
sys.path.append('backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.base')
django.setup()

from apps.sync.moysklad_client import MoySkladClient
from django.conf import settings
import logging

# Настраиваем логирование
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_moysklad_connection():
    """Тестируем соединение с МойСклад API"""
    
    print("=== ТЕСТ СОЕДИНЕНИЯ С МОЙСКЛАД API ===")
    print()
    
    # Проверяем конфигурацию
    config = settings.MOYSKLAD_CONFIG
    print("📋 Конфигурация:")
    print(f"  Base URL: {config['base_url']}")
    print(f"  Token configured: {'✅ Да' if config.get('token') else '❌ Нет'}")
    print(f"  Token length: {len(config.get('token', ''))}")
    print(f"  Default warehouse: {config.get('default_warehouse_id', 'Не установлен')}")
    print(f"  Rate limit: {config.get('rate_limit', 5)} req/sec")
    print(f"  Timeout: {config.get('timeout', 30)} seconds")
    print()
    
    if not config.get('token'):
        print("❌ ОШИБКА: Токен МойСклад не настроен!")
        print("Установите переменную окружения MOYSKLAD_TOKEN")
        return False
    
    try:
        # Создаем клиент
        client = MoySkladClient()
        print("✅ Клиент МойСклад создан")
        
        # Тестируем базовое соединение
        print("\n🔗 Тестируем базовое соединение...")
        if client.test_connection():
            print("✅ Базовое соединение успешно")
        else:
            print("❌ Базовое соединение не удалось")
            return False
        
        # Получаем склады
        print("\n📦 Получаем список складов...")
        warehouses = client.get_warehouses()
        print(f"✅ Получено {len(warehouses)} складов:")
        for warehouse in warehouses[:5]:  # Показываем первые 5
            print(f"  - {warehouse['name']} (ID: {warehouse['id']})")
        
        # Получаем группы товаров
        print("\n📁 Получаем группы товаров...")
        groups = client.get_product_groups()
        print(f"✅ Получено {len(groups)} групп товаров:")
        for group in groups[:5]:  # Показываем первые 5
            print(f"  - {group['name']} (ID: {group['id']})")
        
        # Проверяем настройки склада по умолчанию
        default_warehouse_id = config.get('default_warehouse_id')
        if default_warehouse_id:
            default_warehouse = next(
                (w for w in warehouses if w['id'] == default_warehouse_id), 
                None
            )
            if default_warehouse:
                print(f"\n🏭 Склад по умолчанию: {default_warehouse['name']}")
            else:
                print(f"\n⚠️ Склад по умолчанию с ID {default_warehouse_id} не найден!")
        
        print("\n✅ ВСЕ ТЕСТЫ ПРОШЛИ УСПЕШНО!")
        print("МойСклад API работает корректно.")
        return True
        
    except Exception as e:
        print(f"\n❌ ОШИБКА: {str(e)}")
        print(f"Тип ошибки: {type(e).__name__}")
        
        # Дополнительная диагностика
        if "401" in str(e) or "Unauthorized" in str(e):
            print("\n🔍 ДИАГНОСТИКА:")
            print("- Проверьте корректность токена МойСклад")
            print("- Убедитесь что токен не истек")
            print("- Проверьте права доступа токена")
        elif "timeout" in str(e).lower() or "connection" in str(e).lower():
            print("\n🔍 ДИАГНОСТИКА:")
            print("- Проверьте интернет-соединение")
            print("- Возможны временные проблемы с API МойСклад")
            print("- Попробуйте увеличить timeout в настройках")
        elif "403" in str(e) or "Forbidden" in str(e):
            print("\n🔍 ДИАГНОСТИКА:")
            print("- У токена недостаточно прав доступа")
            print("- Обратитесь к администратору МойСклад")
        
        return False

if __name__ == "__main__":
    success = test_moysklad_connection()
    sys.exit(0 if success else 1)