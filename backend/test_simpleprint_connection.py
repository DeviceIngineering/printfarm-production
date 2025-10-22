#!/usr/bin/env python
"""
Тестовый скрипт для проверки подключения к SimplePrint API
Проверяет доступ к API и получает первые файлы для анализа структуры данных
"""

import os
import sys
import json
import requests
from pathlib import Path

# Добавляем корневую директорию проекта в PYTHONPATH
BASE_DIR = Path(__file__).resolve().parent
sys.path.append(str(BASE_DIR))

# Настраиваем Django окружение
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.base')
import django
django.setup()

from django.conf import settings


def test_simpleprint_connection():
    """
    Тестирование подключения к SimplePrint API
    """
    print("=" * 70)
    print("ТЕСТИРОВАНИЕ ПОДКЛЮЧЕНИЯ К SIMPLEPRINT API")
    print("=" * 70)

    # Получаем конфигурацию
    config = settings.SIMPLEPRINT_CONFIG

    print(f"\n📋 Конфигурация:")
    print(f"  Base URL: {config['base_url']}")
    print(f"  Company ID: {config['company_id']}")
    print(f"  User ID: {config['user_id']}")
    print(f"  Rate Limit: {config['rate_limit']} req/min")
    print(f"  API Token: {config['api_token'][:20]}..." if config['api_token'] else "  API Token: НЕ УСТАНОВЛЕН")

    if not config['api_token']:
        print("\n❌ ОШИБКА: API Token не установлен в .env файле")
        return False

    # Заголовки для запросов
    headers = {
        'X-API-KEY': config['api_token'],
        'Accept': 'application/json',
    }

    # Тест 0: Проверка аутентификации
    print(f"\n\n{'=' * 70}")
    print("ТЕСТ 0: Проверка аутентификации")
    print("=" * 70)

    # Убираем trailing slash из base_url если есть
    base_url = config['base_url'].rstrip('/')
    test_endpoint = f"{base_url}/account/Test"
    print(f"Endpoint: {test_endpoint}")

    try:
        print("Отправка запроса...")
        response = requests.get(test_endpoint, headers=headers, timeout=30)
        print(f"Статус: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print(f"✅ Аутентификация успешна!")
            print(f"Ответ: {json.dumps(data, indent=2, ensure_ascii=False)}")
        else:
            print(f"❌ Ошибка аутентификации: HTTP {response.status_code}")
            print(f"Ответ: {response.text[:500]}")
            return False
    except Exception as e:
        print(f"❌ Ошибка при проверке аутентификации: {e}")
        return False

    # Тест 1: Получение списка файлов и папок
    print(f"\n\n{'=' * 70}")
    print("ТЕСТ 1: Получение списка файлов и папок")
    print("=" * 70)

    endpoint = f"{base_url}/files/GetFiles"
    print(f"Endpoint: {endpoint}")

    try:
        print("Отправка запроса...")
        response = requests.get(endpoint, headers=headers, timeout=30)

        print(f"Статус: {response.status_code}")

        if response.status_code == 200:
            print("✅ Подключение успешно!")

            data = response.json()

            # Анализ структуры ответа
            print(f"\n📊 Структура ответа:")
            print(f"  Тип данных: {type(data)}")

            if isinstance(data, dict):
                print(f"  Ключи верхнего уровня: {list(data.keys())}")

                # Подробный анализ каждого ключа
                for key, value in data.items():
                    print(f"\n  📁 Ключ '{key}':")
                    print(f"     Тип: {type(value)}")
                    if isinstance(value, list):
                        print(f"     Количество элементов: {len(value)}")
                        if len(value) > 0:
                            print(f"     Пример первого элемента:")
                            print(f"     {json.dumps(value[0], indent=8, ensure_ascii=False)}")
                    elif isinstance(value, dict):
                        print(f"     Ключи: {list(value.keys())}")
                    else:
                        print(f"     Значение: {value}")

            # Сохранение полного ответа в файл
            output_file = BASE_DIR / 'simpleprint_test_response.json'
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            print(f"\n💾 Полный ответ сохранен в: {output_file}")

            return True

        else:
            print(f"❌ Ошибка подключения: HTTP {response.status_code}")
            print(f"Ответ сервера: {response.text[:500]}")
            return False

    except requests.exceptions.RequestException as e:
        print(f"❌ Ошибка сети: {e}")
        return False
    except json.JSONDecodeError as e:
        print(f"❌ Ошибка парсинга JSON: {e}")
        print(f"Ответ сервера: {response.text[:500]}")
        return False
    except Exception as e:
        print(f"❌ Неожиданная ошибка: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_folder_details():
    """
    Тестирование получения деталей папки (если есть папки)
    """
    print(f"\n\n{'=' * 70}")
    print("ТЕСТ 2: Получение деталей папки (опционально)")
    print("=" * 70)
    print("⏭️  Пропускаем - сначала нужно получить список папок из Теста 1")


if __name__ == '__main__':
    print("\n🚀 Запуск тестирования SimplePrint API...\n")

    success = test_simpleprint_connection()

    if success:
        test_folder_details()
        print("\n\n✅ Тестирование завершено успешно!")
        print("📄 Проверьте файл simpleprint_test_response.json для детального анализа")
    else:
        print("\n\n❌ Тестирование завершилось с ошибками")
        sys.exit(1)

    print("\n" + "=" * 70)
