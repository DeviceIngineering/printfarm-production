"""
Безопасный тест синхронизации с МойСклад
"""
import os
import sys
import django

# Добавляем путь к проекту
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Настраиваем Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.local_no_celery')
django.setup()

from apps.sync.moysklad_client import MoySkladClient

def test_connection():
    """Тестируем подключение к МойСклад"""
    print("=== Тест подключения к МойСклад ===")
    
    try:
        client = MoySkladClient()
        
        # Получаем список складов
        print("\n1. Получение списка складов...")
        warehouses = client.get_warehouses()
        print(f"✅ Найдено складов: {len(warehouses)}")
        
        for i, warehouse in enumerate(warehouses[:3], 1):
            print(f"   {i}. {warehouse.get('name', 'Без названия')} (ID: {warehouse.get('id')})")
        
        # Проверяем токен
        print("\n2. Проверка токена...")
        context_response = client._make_request('context/employee')
        if context_response:
            print(f"✅ Токен валидный. Пользователь: {context_response.get('name', 'Unknown')}")
        
        print("\n✅ Тест подключения прошел успешно!")
        return True
        
    except Exception as e:
        print(f"\n❌ Ошибка: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_connection()