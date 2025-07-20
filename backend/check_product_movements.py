#!/usr/bin/env python
"""
Проверка движений товара 376-41401 для понимания истории остатков
"""
import os
import sys
import django
from datetime import datetime, timedelta

# Настройка Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.sync.moysklad_client import MoySkladClient

def main():
    print("=== Анализ движений товара 376-41401 ===\n")
    
    client = MoySkladClient()
    product_id = '03d80ab8-7a3d-11ef-0a80-040c003525fc'
    
    # Проверяем историю движений товара за последние 3 месяца
    date_to = datetime.now()
    date_from = date_to - timedelta(days=90)
    
    print(f"Период анализа: {date_from.strftime('%Y-%m-%d')} - {date_to.strftime('%Y-%m-%d')}")
    
    try:
        # Попробуем получить движения товара
        print("\n1. Проверяем отчет по движениям товара...")
        
        # Запрос к API отчета по движениям
        params = {
            'filter': f'product.id={product_id}',
            'momentFrom': date_from.strftime('%Y-%m-%d %H:%M:%S'),
            'momentTo': date_to.strftime('%Y-%m-%d %H:%M:%S'),
            'limit': 100
        }
        
        try:
            movements = client._make_request('GET', 'report/stock/byoperations', params=params)
            if movements.get('rows'):
                print(f"✅ Найдено {len(movements['rows'])} движений товара:")
                for i, movement in enumerate(movements['rows'][:10], 1):  # Показываем первые 10
                    print(f"  {i}. {movement.get('moment', 'Неизвестно')} - {movement.get('operation', {}).get('name', 'Операция')}")
            else:
                print("❌ Движений товара не найдено за указанный период")
        except Exception as e:
            print(f"❌ Ошибка получения движений: {e}")
        
        print("\n2. Проверяем отчет по остаткам и оборотам...")
        
        # Альтернативный запрос - оборотно-сальдовая ведомость
        warehouse_id = '241ed919-a631-11ee-0a80-07a9000bb947'  # Адресный склад
        params = {
            'filter': f'product.id={product_id};store.id={warehouse_id}',
            'momentFrom': date_from.strftime('%Y-%m-%d %H:%M:%S'),
            'momentTo': date_to.strftime('%Y-%m-%d %H:%M:%S'),
            'limit': 10
        }
        
        try:
            turnover = client._make_request('GET', 'report/turnover/bystore', params=params)
            if turnover.get('rows'):
                row = turnover['rows'][0]
                print(f"✅ Оборотно-сальдовая ведомость:")
                print(f"  Остаток на начало: {row.get('onPeriodStart', {}).get('quantity', 0)}")
                print(f"  Поступило: {row.get('income', {}).get('quantity', 0)}")
                print(f"  Отгружено: {row.get('outcome', {}).get('quantity', 0)}")
                print(f"  Остаток на конец: {row.get('onPeriodEnd', {}).get('quantity', 0)}")
            else:
                print("❌ Данные по оборотам не найдены")
        except Exception as e:
            print(f"❌ Ошибка получения оборотов: {e}")
        
        print("\n3. Проверяем последние документы с этим товаром...")
        
        # Ищем документы, содержащие этот товар
        try:
            # Получаем последние накладные
            params = {
                'filter': f'positions.assortment.id={product_id}',
                'order': 'moment,desc',
                'limit': 5
            }
            
            # Проверяем разные типы документов
            doc_types = [
                ('demand', 'Отгрузки'),
                ('supply', 'Приходы'),
                ('move', 'Перемещения'),
                ('inventory', 'Инвентаризации')
            ]
            
            for doc_type, doc_name in doc_types:
                try:
                    docs = client._make_request('GET', f'entity/{doc_type}', params=params)
                    if docs.get('rows'):
                        print(f"  📋 {doc_name}: найдено {len(docs['rows'])} документов")
                        for doc in docs['rows'][:2]:  # Показываем последние 2
                            print(f"    - {doc.get('moment', 'Неизвестно')}: {doc.get('name', 'Без названия')}")
                    else:
                        print(f"  📋 {doc_name}: документов не найдено")
                except Exception as e:
                    print(f"  📋 {doc_name}: ошибка - {e}")
        except Exception as e:
            print(f"❌ Ошибка поиска документов: {e}")
            
    except Exception as e:
        print(f"❌ Общая ошибка: {e}")
    
    print("\n=== Рекомендации ===")
    print("1. Проверьте в МойСклад веб-интерфейсе:")
    print("   - Остатки товара 376-41401 на всех складах")
    print("   - Историю движений товара")
    print("   - Последние документы по товару")
    print("\n2. Если товар должен быть в наличии:")
    print("   - Проведите инвентаризацию")
    print("   - Создайте документ поступления")
    print("   - Убедитесь, что остатки > 0")
    print("\n3. После добавления остатков запустите синхронизацию")

if __name__ == '__main__':
    main()