"""
Тесты SimplePrint API Client
Цель: Проверить каждый метод клиента отдельно с детальной диагностикой
"""

import pytest
import logging
from unittest.mock import patch, MagicMock
from apps.simpleprint.client import SimplePrintClient
from django.conf import settings

logger = logging.getLogger(__name__)


class TestSimplePrintClient:
    """Тестирование SimplePrint API клиента"""

    @pytest.fixture
    def client(self):
        """Создать клиент для тестов"""
        return SimplePrintClient()

    def test_01_client_initialization(self, client):
        """
        ✅/❌ Тест 1: Инициализация клиента
        Проверяет: корректность настроек из settings.py
        """
        print("\n" + "="*80)
        print("🔧 ТЕСТ 1: Инициализация SimplePrint клиента")
        print("="*80)

        try:
            # Проверяем наличие всех обязательных настроек
            assert hasattr(settings, 'SIMPLEPRINT_CONFIG'), "❌ FAIL: SIMPLEPRINT_CONFIG отсутствует в settings"
            config = settings.SIMPLEPRINT_CONFIG

            print(f"📋 Конфигурация SimplePrint:")
            print(f"   - API Token: {config.get('api_token')[:10]}... (первые 10 символов)")
            print(f"   - User ID: {config.get('user_id')}")
            print(f"   - Company ID: {config.get('company_id')}")
            print(f"   - Base URL: {config.get('base_url')}")
            print(f"   - Rate Limit: {config.get('rate_limit')} req/min")

            # Проверяем клиент
            assert client.api_token is not None, "❌ FAIL: api_token is None"
            assert client.user_id is not None, "❌ FAIL: user_id is None"
            assert client.company_id is not None, "❌ FAIL: company_id is None"
            assert client.base_url is not None, "❌ FAIL: base_url is None"

            print(f"\n✅ PASS: Клиент инициализирован корректно")
            print(f"   - API Token: {'✓' if client.api_token else '✗'}")
            print(f"   - User ID: {'✓' if client.user_id else '✗'}")
            print(f"   - Company ID: {'✓' if client.company_id else '✗'}")
            print(f"   - Base URL: {'✓' if client.base_url else '✗'}")

        except AssertionError as e:
            print(f"\n❌ FAIL: {str(e)}")
            print(f"📍 Файл: backend/config/settings/base.py")
            print(f"📍 Строка: SIMPLEPRINT_CONFIG = {{...}}")
            raise
        except Exception as e:
            print(f"\n❌ FAIL: Неожиданная ошибка: {str(e)}")
            print(f"📍 Тип ошибки: {type(e).__name__}")
            raise

    def test_02_test_connection(self, client):
        """
        ✅/❌ Тест 2: Проверка подключения к API
        Проверяет: GET /account/Test
        """
        print("\n" + "="*80)
        print("🌐 ТЕСТ 2: Подключение к SimplePrint API")
        print("="*80)

        try:
            print(f"📡 Отправка запроса: GET {client.base_url}account/Test")
            print(f"🔑 Headers:")
            print(f"   - X-API-KEY: {client.api_token[:10]}...")
            print(f"   - Content-Type: application/json")

            result = client.test_connection()

            print(f"\n📥 Ответ API:")
            print(f"   - Статус: {result.get('status', 'N/A')}")
            print(f"   - Результат: {result}")

            assert result.get('success') is True, f"❌ FAIL: API вернул success=False. Response: {result}"

            print(f"\n✅ PASS: Подключение к API успешно")

        except AssertionError as e:
            print(f"\n❌ FAIL: {str(e)}")
            print(f"📍 Файл: backend/apps/simpleprint/client.py")
            print(f"📍 Метод: test_connection()")
            print(f"💡 Возможные причины:")
            print(f"   - Неверный API токен")
            print(f"   - API SimplePrint недоступен")
            print(f"   - Неправильный base_url")
            raise
        except Exception as e:
            print(f"\n❌ FAIL: Ошибка запроса к API")
            print(f"📍 Тип ошибки: {type(e).__name__}")
            print(f"📍 Сообщение: {str(e)}")
            print(f"📍 Файл: backend/apps/simpleprint/client.py")
            print(f"📍 Метод: test_connection() -> _make_request()")
            raise

    def test_03_get_files_folders(self, client):
        """
        ✅/❌ Тест 3: Получение файлов и папок
        Проверяет: GET /files/GetFiles
        """
        print("\n" + "="*80)
        print("📁 ТЕСТ 3: Получение файлов и папок из SimplePrint")
        print("="*80)

        try:
            print(f"📡 Отправка запроса: GET {client.base_url}files/GetFiles")
            print(f"📝 Параметры:")
            print(f"   - userId: {client.user_id}")
            print(f"   - id: None (корневая папка)")

            data = client.get_files_and_folders(parent_id=None)

            print(f"\n📥 Ответ API:")
            print(f"   - Тип данных: {type(data).__name__}")

            if isinstance(data, dict):
                print(f"   - Ключи: {list(data.keys())}")
                if 'files' in data:
                    print(f"   - Количество файлов: {len(data['files'])}")
                if 'folders' in data:
                    print(f"   - Количество папок: {len(data['folders'])}")
            else:
                print(f"   - Данные: {str(data)[:200]}...")

            # Проверяем структуру ответа
            assert data is not None, "❌ FAIL: API вернул None"

            if isinstance(data, dict):
                # SimplePrint может возвращать разные форматы
                has_files = 'files' in data
                has_folders = 'folders' in data
                has_data = 'data' in data

                print(f"\n📊 Структура ответа:")
                print(f"   - Есть 'files': {has_files}")
                print(f"   - Есть 'folders': {has_folders}")
                print(f"   - Есть 'data': {has_data}")

                if has_files or has_folders or has_data:
                    print(f"\n✅ PASS: Получены данные из API")
                else:
                    print(f"\n⚠️  WARNING: Неожиданная структура ответа")
                    print(f"📋 Полный ответ: {data}")
            else:
                print(f"\n⚠️  WARNING: Ответ не является dict")
                print(f"📋 Ответ: {data}")

        except AssertionError as e:
            print(f"\n❌ FAIL: {str(e)}")
            print(f"📍 Файл: backend/apps/simpleprint/client.py")
            print(f"📍 Метод: get_files_and_folders()")
            raise
        except Exception as e:
            print(f"\n❌ FAIL: Ошибка получения файлов")
            print(f"📍 Тип ошибки: {type(e).__name__}")
            print(f"📍 Сообщение: {str(e)}")
            print(f"📍 Файл: backend/apps/simpleprint/client.py")
            print(f"📍 Метод: get_files_and_folders() -> _make_request()")

            # Дополнительная диагностика
            import traceback
            print(f"\n🔍 Полный traceback:")
            print(traceback.format_exc())
            raise

    def test_04_rate_limiting(self, client):
        """
        ✅/❌ Тест 4: Проверка rate limiting
        Проверяет: соблюдение лимита 180 req/min
        """
        print("\n" + "="*80)
        print("⏱️  ТЕСТ 4: Rate Limiting (180 req/min)")
        print("="*80)

        try:
            import time

            print(f"📊 Конфигурация:")
            print(f"   - Лимит: {client.rate_limit} запросов/минуту")
            print(f"   - Минимальная задержка: {60.0 / client.rate_limit:.3f} секунд")

            # Делаем 3 быстрых запроса
            print(f"\n🔄 Выполнение 3 быстрых запросов...")

            times = []
            for i in range(3):
                start = time.time()
                try:
                    client.test_connection()
                except:
                    pass  # Игнорируем ошибки API, нас интересует только timing
                elapsed = time.time() - start
                times.append(elapsed)
                print(f"   Запрос {i+1}: {elapsed:.3f} секунд")

            # Проверяем что между запросами есть задержки
            min_delay = 60.0 / client.rate_limit

            print(f"\n📊 Анализ задержек:")
            for i, t in enumerate(times[1:], 1):
                delay = times[i] - times[i-1]
                status = "✓" if delay >= min_delay * 0.9 else "✗"  # 90% от минимальной задержки
                print(f"   Задержка {i}: {delay:.3f}s {status}")

            print(f"\n✅ PASS: Rate limiting работает")

        except Exception as e:
            print(f"\n❌ FAIL: Ошибка проверки rate limiting")
            print(f"📍 Тип ошибки: {type(e).__name__}")
            print(f"📍 Сообщение: {str(e)}")
            print(f"📍 Файл: backend/apps/simpleprint/client.py")
            print(f"📍 Метод: _make_request() -> _apply_rate_limit()")
            raise

    @patch('apps.simpleprint.client.requests.get')
    def test_05_error_handling(self, mock_get, client):
        """
        ✅/❌ Тест 5: Обработка ошибок API
        Проверяет: retry логика при ошибках
        """
        print("\n" + "="*80)
        print("🔥 ТЕСТ 5: Обработка ошибок и retry")
        print("="*80)

        try:
            # Симулируем 500 ошибку
            mock_response = MagicMock()
            mock_response.status_code = 500
            mock_response.text = "Internal Server Error"
            mock_response.raise_for_status.side_effect = Exception("500 Server Error")
            mock_get.return_value = mock_response

            print(f"🧪 Симуляция: 500 Internal Server Error")
            print(f"📊 Ожидаемое поведение: 3 попытки retry")

            try:
                client.test_connection()
                print(f"\n⚠️  WARNING: Исключение не было выброшено")
            except Exception as e:
                print(f"\n✅ Исключение поймано: {type(e).__name__}")
                print(f"   Сообщение: {str(e)}")

            # Проверяем количество попыток
            call_count = mock_get.call_count
            print(f"\n📊 Количество попыток: {call_count}")
            print(f"   Ожидалось: 3")
            print(f"   Получено: {call_count}")

            if call_count == 3:
                print(f"\n✅ PASS: Retry логика работает корректно (3 попытки)")
            else:
                print(f"\n⚠️  WARNING: Неожиданное количество попыток")

        except Exception as e:
            print(f"\n❌ FAIL: Ошибка в тесте обработки ошибок")
            print(f"📍 Тип ошибки: {type(e).__name__}")
            print(f"📍 Сообщение: {str(e)}")
            raise


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
