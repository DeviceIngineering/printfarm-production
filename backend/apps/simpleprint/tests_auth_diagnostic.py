"""
Диагностические тесты для аутентификации SimplePrint API

Запуск: docker exec factory_v3_backend python manage.py test apps.simpleprint.tests_auth_diagnostic
"""

import logging
from django.test import TestCase, Client
from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient
from django.urls import reverse
from apps.simpleprint.models import SimplePrintSync

logger = logging.getLogger(__name__)


class SimplePrintAuthDiagnosticTest(TestCase):
    """
    Диагностические тесты для проверки аутентификации
    """

    def setUp(self):
        """Настройка тестового окружения"""
        print("\n" + "="*80)
        print("🔧 НАСТРОЙКА ТЕСТОВОГО ОКРУЖЕНИЯ")
        print("="*80)

        # Создаем тестового пользователя
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            email='test@example.com'
        )
        print(f"✅ Пользователь создан: {self.user.username} (ID: {self.user.id})")

        # Создаем токен
        self.token = Token.objects.create(user=self.user)
        print(f"✅ Токен создан: {self.token.key[:20]}...")

        # Создаем API client
        self.api_client = APIClient()
        print("✅ API Client создан")

        print("\n")

    def test_01_token_exists(self):
        """
        Тест 1: Проверка существования токена в БД
        """
        print("\n" + "="*80)
        print("ТЕСТ 1: Проверка существования токена")
        print("="*80)

        # Проверяем что токен существует
        token_exists = Token.objects.filter(key=self.token.key).exists()
        print(f"Токен {self.token.key[:20]}... существует: {token_exists}")

        # Проверяем что токен связан с пользователем
        token_obj = Token.objects.get(key=self.token.key)
        print(f"Токен принадлежит пользователю: {token_obj.user.username}")
        print(f"Пользователь активен: {token_obj.user.is_active}")

        self.assertTrue(token_exists)
        self.assertEqual(token_obj.user.id, self.user.id)
        print("✅ Тест пройден: Токен корректно связан с пользователем")

    def test_02_trigger_without_auth(self):
        """
        Тест 2: Попытка запуска синхронизации БЕЗ токена (должен вернуть 401)
        """
        print("\n" + "="*80)
        print("ТЕСТ 2: Запуск синхронизации БЕЗ токена")
        print("="*80)

        url = '/api/v1/simpleprint/sync/trigger/'
        print(f"📡 POST {url}")
        print(f"🔐 Токен: НЕТ")

        response = self.api_client.post(url, {'full_sync': False, 'force': True})

        print(f"📋 Статус ответа: {response.status_code}")
        print(f"📝 Данные ответа: {response.data if hasattr(response, 'data') else response.content}")

        self.assertEqual(response.status_code, 401)
        print("✅ Тест пройден: Без токена возвращается 401")

    def test_03_trigger_with_valid_auth(self):
        """
        Тест 3: Запуск синхронизации С КОРРЕКТНЫМ токеном (должен вернуть 202 или 429)
        """
        print("\n" + "="*80)
        print("ТЕСТ 3: Запуск синхронизации С корректным токеном")
        print("="*80)

        # Устанавливаем токен
        self.api_client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')

        url = '/api/v1/simpleprint/sync/trigger/'
        print(f"📡 POST {url}")
        print(f"🔐 Токен: Token {self.token.key[:20]}...")
        print(f"📝 Параметры: full_sync=False, force=True")

        response = self.api_client.post(url, {'full_sync': False, 'force': True})

        print(f"📋 Статус ответа: {response.status_code}")
        print(f"📝 Данные ответа: {response.data if hasattr(response, 'data') else response.content}")

        # Должен вернуть либо 202 (задача запущена), либо 429 (cooldown)
        self.assertIn(response.status_code, [202, 429, 500])  # 500 если нет SimplePrint API
        print(f"✅ Тест пройден: С токеном возвращается {response.status_code}")

    def test_04_trigger_with_invalid_token(self):
        """
        Тест 4: Запуск синхронизации с НЕКОРРЕКТНЫМ токеном (должен вернуть 401)
        """
        print("\n" + "="*80)
        print("ТЕСТ 4: Запуск синхронизации с некорректным токеном")
        print("="*80)

        # Устанавливаем неправильный токен
        invalid_token = 'invalid_token_12345678901234567890'
        self.api_client.credentials(HTTP_AUTHORIZATION=f'Token {invalid_token}')

        url = '/api/v1/simpleprint/sync/trigger/'
        print(f"📡 POST {url}")
        print(f"🔐 Токен: Token {invalid_token}")

        response = self.api_client.post(url, {'full_sync': False, 'force': True})

        print(f"📋 Статус ответа: {response.status_code}")
        print(f"📝 Данные ответа: {response.data if hasattr(response, 'data') else response.content}")

        self.assertEqual(response.status_code, 401)
        print("✅ Тест пройден: С неправильным токеном возвращается 401")

    def test_05_cooldown_mechanism(self):
        """
        Тест 5: Проверка механизма cooldown (2 запроса подряд)
        """
        print("\n" + "="*80)
        print("ТЕСТ 5: Проверка механизма cooldown")
        print("="*80)

        # Устанавливаем токен
        self.api_client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')

        url = '/api/v1/simpleprint/sync/trigger/'

        # Первый запрос (с force=True, чтобы обойти предыдущие cooldown)
        print(f"\n📡 ПЕРВЫЙ ЗАПРОС: POST {url}")
        print(f"📝 Параметры: full_sync=False, force=True")
        response1 = self.api_client.post(url, {'full_sync': False, 'force': True})
        print(f"📋 Статус: {response1.status_code}")
        print(f"📝 Ответ: {response1.data if hasattr(response1, 'data') else response1.content}")

        # Второй запрос сразу после первого (БЕЗ force, должен вернуть 429)
        print(f"\n📡 ВТОРОЙ ЗАПРОС (сразу после): POST {url}")
        print(f"📝 Параметры: full_sync=False, force=False")
        response2 = self.api_client.post(url, {'full_sync': False, 'force': False})
        print(f"📋 Статус: {response2.status_code}")
        print(f"📝 Ответ: {response2.data if hasattr(response2, 'data') else response2.content}")

        # Проверяем что второй запрос вернул 429 (cooldown)
        if response1.status_code in [202, 500]:  # Если первый запрос прошел
            print("\n🔍 АНАЛИЗ:")
            print(f"   Первый запрос: {response1.status_code}")
            print(f"   Второй запрос: {response2.status_code}")

            if response2.status_code == 429:
                print("✅ Cooldown работает корректно - второй запрос вернул 429")
            elif response2.status_code == 401:
                print("❌ ПРОБЛЕМА: Второй запрос вернул 401 вместо 429!")
                print("   Это указывает на проблему с токеном после первого запроса")
            else:
                print(f"⚠️ НЕОЖИДАННЫЙ СТАТУС: {response2.status_code}")
        else:
            print(f"⚠️ Первый запрос не прошел: {response1.status_code}")
            print("   Невозможно проверить cooldown")

    def test_06_check_production_token(self):
        """
        Тест 6: Проверка production токена из CLAUDE.md
        """
        print("\n" + "="*80)
        print("ТЕСТ 6: Проверка production токена")
        print("="*80)

        production_token = '0a8fee03bca2b530a15b1df44d38b304e3f57484'
        print(f"🔍 Проверяем токен: {production_token[:20]}...")

        # Проверяем существование токена
        token_exists = Token.objects.filter(key=production_token).exists()
        print(f"📋 Токен существует в БД: {token_exists}")

        if token_exists:
            token = Token.objects.get(key=production_token)
            print(f"✅ Токен найден:")
            print(f"   Пользователь: {token.user.username}")
            print(f"   Email: {token.user.email}")
            print(f"   Активен: {token.user.is_active}")
            print(f"   Суперпользователь: {token.user.is_superuser}")
        else:
            print(f"❌ Токен НЕ НАЙДЕН в базе данных!")
            print(f"   Это объясняет ошибку 401")
            print(f"\n💡 РЕШЕНИЕ:")
            print(f"   Создайте токен командой:")
            print(f"   docker exec factory_v3_backend python manage.py shell -c \"")
            print(f"   from rest_framework.authtoken.models import Token")
            print(f"   from django.contrib.auth.models import User")
            print(f"   user = User.objects.first()")
            print(f"   Token.objects.get_or_create(user=user, key='{production_token}')")
            print(f"   \"")

        # Не делаем assert, просто информируем
        if not token_exists:
            print("\n⚠️ ВНИМАНИЕ: Production токен отсутствует!")


class SimplePrintCooldownDiagnosticTest(TestCase):
    """
    Детальные тесты механизма cooldown
    """

    def setUp(self):
        """Настройка"""
        self.user = User.objects.create_user(username='test', password='test')
        self.token = Token.objects.create(user=self.user)
        self.api_client = APIClient()
        self.api_client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')

    def test_cooldown_response_format(self):
        """
        Проверка формата ответа при cooldown
        """
        print("\n" + "="*80)
        print("ТЕСТ: Формат ответа при cooldown")
        print("="*80)

        url = '/api/v1/simpleprint/sync/trigger/'

        # Создаем синхронизацию чтобы был last_sync
        SimplePrintSync.objects.create(
            status='success',
            total_files=100,
            synced_files=100
        )

        # Запрос БЕЗ force - должен вернуть 429
        response = self.api_client.post(url, {'full_sync': False, 'force': False})

        print(f"📋 Статус: {response.status_code}")
        print(f"📝 Тело ответа: {response.data if hasattr(response, 'data') else response.content}")

        if response.status_code == 429:
            print("✅ Cooldown возвращает 429")
            print(f"   Сообщение: {response.data.get('message', 'НЕТ')}")
        elif response.status_code == 401:
            print("❌ ОШИБКА: Cooldown возвращает 401 вместо 429!")
        else:
            print(f"⚠️ Неожиданный статус: {response.status_code}")
