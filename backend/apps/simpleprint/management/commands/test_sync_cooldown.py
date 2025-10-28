"""
Management команда для тестирования cooldown механизма синхронизации

Запуск: docker exec factory_v3_backend python manage.py test_sync_cooldown
"""

import time
import logging
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient
from apps.simpleprint.models import SimplePrintSync

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Тестирование cooldown механизма синхронизации SimplePrint'

    def add_arguments(self, parser):
        parser.add_argument(
            '--token',
            type=str,
            default='0a8fee03bca2b530a15b1df44d38b304e3f57484',
            help='Токен для тестирования (по умолчанию production токен)'
        )

    def handle(self, *args, **options):
        token_key = options['token']

        self.stdout.write("\n" + "="*80)
        self.stdout.write(self.style.SUCCESS("🔬 ТЕСТ COOLDOWN МЕХАНИЗМА SIMPLEPRINT"))
        self.stdout.write("="*80 + "\n")

        # ============================================================================
        # ШАГ 1: Проверка токена
        # ============================================================================
        self.stdout.write(self.style.WARNING("📋 ШАГ 1: Проверка токена в БД"))
        self.stdout.write("-" * 80)

        try:
            token = Token.objects.get(key=token_key)
            self.stdout.write(self.style.SUCCESS(f"✅ Токен найден: {token_key[:20]}..."))
            self.stdout.write(f"   Пользователь: {token.user.username}")
            self.stdout.write(f"   Email: {token.user.email}")
            self.stdout.write(f"   Активен: {token.user.is_active}")
        except Token.DoesNotExist:
            self.stdout.write(self.style.ERROR(f"❌ Токен НЕ НАЙДЕН: {token_key[:20]}..."))
            self.stdout.write("\n💡 Создаю токен...")

            # Создаем токен
            user = User.objects.first()
            if not user:
                user = User.objects.create_user(
                    username='testadmin',
                    password='testpass123',
                    email='admin@printfarm.local'
                )
                self.stdout.write(f"   Создан пользователь: {user.username}")

            token = Token.objects.create(user=user, key=token_key)
            self.stdout.write(self.style.SUCCESS(f"✅ Токен создан для {user.username}"))

        self.stdout.write("")

        # ============================================================================
        # ШАГ 2: Очистка предыдущих синхронизаций для чистого теста
        # ============================================================================
        self.stdout.write(self.style.WARNING("📋 ШАГ 2: Подготовка тестового окружения"))
        self.stdout.write("-" * 80)

        old_syncs = SimplePrintSync.objects.all().count()
        self.stdout.write(f"Найдено синхронизаций: {old_syncs}")
        self.stdout.write("⚠️ НЕ удаляем старые синхронизации (для реалистичного теста)")
        self.stdout.write("")

        # ============================================================================
        # ШАГ 3: API Client
        # ============================================================================
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f'Token {token_key}')
        url = '/api/v1/simpleprint/sync/trigger/'

        # ============================================================================
        # ТЕСТ 1: Первый запрос БЕЗ force (должен либо пройти, либо вернуть 429)
        # ============================================================================
        self.stdout.write(self.style.WARNING("📋 ТЕСТ 1: Первый запрос БЕЗ force"))
        self.stdout.write("-" * 80)

        response1 = client.post(url, {'full_sync': False, 'force': False}, format='json')

        self.stdout.write(f"📡 POST {url}")
        self.stdout.write(f"📝 Body: {{'full_sync': False, 'force': False}}")
        self.stdout.write(f"🔐 Token: Token {token_key[:20]}...")
        self.stdout.write(f"\n📋 Статус ответа: {response1.status_code}")
        self.stdout.write(f"📝 Тело ответа: {response1.data if hasattr(response1, 'data') else response1.content}")

        if response1.status_code == 429:
            self.stdout.write(self.style.WARNING("⏱️ Cooldown активен (прошло < 5 минут с последней синхронизации)"))
            self.stdout.write("   Это ОЖИДАЕМОЕ поведение если синхронизация была недавно")
        elif response1.status_code == 202:
            self.stdout.write(self.style.SUCCESS("✅ Синхронизация запущена"))
        elif response1.status_code == 401:
            self.stdout.write(self.style.ERROR("❌ ОШИБКА: Получен 401 (проблема с токеном!)"))
        elif response1.status_code == 500:
            self.stdout.write(self.style.ERROR("❌ ОШИБКА: 500 (проблема с SimplePrint API или Celery)"))
        else:
            self.stdout.write(self.style.ERROR(f"❌ НЕОЖИДАННЫЙ СТАТУС: {response1.status_code}"))

        self.stdout.write("")

        # ============================================================================
        # ТЕСТ 2: Второй запрос сразу БЕЗ force (ДОЛЖЕН вернуть 429)
        # ============================================================================
        self.stdout.write(self.style.WARNING("📋 ТЕСТ 2: Второй запрос сразу БЕЗ force (ожидаем 429)"))
        self.stdout.write("-" * 80)

        time.sleep(1)  # Небольшая задержка

        response2 = client.post(url, {'full_sync': False, 'force': False}, format='json')

        self.stdout.write(f"📡 POST {url}")
        self.stdout.write(f"📝 Body: {{'full_sync': False, 'force': False}}")
        self.stdout.write(f"\n📋 Статус ответа: {response2.status_code}")
        self.stdout.write(f"📝 Тело ответа: {response2.data if hasattr(response2, 'data') else response2.content}")

        if response2.status_code == 429:
            self.stdout.write(self.style.SUCCESS("✅ COOLDOWN РАБОТАЕТ: Получен 429"))
            if hasattr(response2, 'data'):
                message = response2.data.get('message', '')
                self.stdout.write(f"   Сообщение: {message}")
        elif response2.status_code == 401:
            self.stdout.write(self.style.ERROR("❌ КРИТИЧЕСКАЯ ОШИБКА: Получен 401 вместо 429!"))
            self.stdout.write("   Это указывает на проблему с аутентификацией при cooldown")
        elif response2.status_code == 202:
            self.stdout.write(self.style.ERROR("❌ ОШИБКА: Cooldown НЕ РАБОТАЕТ (получен 202 вместо 429)"))
        else:
            self.stdout.write(self.style.ERROR(f"❌ НЕОЖИДАННЫЙ СТАТУС: {response2.status_code}"))

        self.stdout.write("")

        # ============================================================================
        # ТЕСТ 3: Третий запрос С force=True (ДОЛЖЕН пройти даже при cooldown)
        # ============================================================================
        self.stdout.write(self.style.WARNING("📋 ТЕСТ 3: Третий запрос С force=True (ожидаем 202)"))
        self.stdout.write("-" * 80)

        time.sleep(1)

        response3 = client.post(url, {'full_sync': False, 'force': True}, format='json')

        self.stdout.write(f"📡 POST {url}")
        self.stdout.write(f"📝 Body: {{'full_sync': False, 'force': True}}")
        self.stdout.write(f"\n📋 Статус ответа: {response3.status_code}")
        self.stdout.write(f"📝 Тело ответа: {response3.data if hasattr(response3, 'data') else response3.content}")

        if response3.status_code == 202:
            self.stdout.write(self.style.SUCCESS("✅ FORCE РАБОТАЕТ: Получен 202 (синхронизация запущена)"))
            if hasattr(response3, 'data'):
                task_id = response3.data.get('task_id', 'N/A')
                self.stdout.write(f"   Task ID: {task_id}")
        elif response3.status_code == 429:
            self.stdout.write(self.style.ERROR("❌ КРИТИЧЕСКАЯ ОШИБКА: Force НЕ РАБОТАЕТ (получен 429)"))
            self.stdout.write("   Параметр force=True игнорируется!")
        elif response3.status_code == 401:
            self.stdout.write(self.style.ERROR("❌ ОШИБКА: Получен 401 (проблема с токеном!)"))
        elif response3.status_code == 500:
            self.stdout.write(self.style.ERROR("❌ ОШИБКА: 500 (проблема с SimplePrint API или Celery)"))
        else:
            self.stdout.write(self.style.ERROR(f"❌ НЕОЖИДАННЫЙ СТАТУС: {response3.status_code}"))

        self.stdout.write("")

        # ============================================================================
        # ИТОГИ
        # ============================================================================
        self.stdout.write(self.style.SUCCESS("\n" + "="*80))
        self.stdout.write(self.style.SUCCESS("📊 ИТОГИ ТЕСТИРОВАНИЯ"))
        self.stdout.write(self.style.SUCCESS("="*80))

        self.stdout.write(f"\nТест 1 (БЕЗ force): {response1.status_code}")
        self.stdout.write(f"Тест 2 (БЕЗ force, повтор): {response2.status_code}")
        self.stdout.write(f"Тест 3 (С force=True): {response3.status_code}")

        # Анализ результатов
        self.stdout.write("\n🔍 АНАЛИЗ:")

        if response2.status_code == 401:
            self.stdout.write(self.style.ERROR("\n❌ ПРОБЛЕМА НАЙДЕНА: При cooldown возвращается 401 вместо 429"))
            self.stdout.write("\nВОЗМОЖНЫЕ ПРИЧИНЫ:")
            self.stdout.write("1. Токен некорректен в БД")
            self.stdout.write("2. Middleware изменяет статус ответа")
            self.stdout.write("3. Проблема с CORS preflight")
            self.stdout.write("\nРЕКОМЕНДАЦИИ:")
            self.stdout.write("- Проверить логи Django (docker logs -f factory_v3_backend)")
            self.stdout.write("- Проверить CORS настройки в settings.py")
            self.stdout.write("- Добавить логирование в views.py:395-402")

        elif response2.status_code == 429 and response3.status_code != 202:
            self.stdout.write(self.style.ERROR("\n❌ ПРОБЛЕМА: Force не работает"))
            self.stdout.write("\nВОЗМОЖНЫЕ ПРИЧИНЫ:")
            self.stdout.write("1. Serializer не парсит параметр force")
            self.stdout.write("2. Условие `if not force:` работает неправильно")
            self.stdout.write("\nРЕКОМЕНДАЦИИ:")
            self.stdout.write("- Проверить TriggerSyncSerializer в serializers.py")
            self.stdout.write("- Добавить логирование в views.py:389")

        elif response2.status_code == 429 and response3.status_code == 202:
            self.stdout.write(self.style.SUCCESS("\n✅ ВСЁ РАБОТАЕТ КОРРЕКТНО!"))
            self.stdout.write("\nCooldown работает правильно:")
            self.stdout.write("- БЕЗ force возвращается 429")
            self.stdout.write("- С force синхронизация запускается")

        else:
            self.stdout.write(self.style.WARNING("\n⚠️ Результаты неоднозначны"))
            self.stdout.write("Требуется дополнительная диагностика")

        self.stdout.write("\n" + "="*80 + "\n")
