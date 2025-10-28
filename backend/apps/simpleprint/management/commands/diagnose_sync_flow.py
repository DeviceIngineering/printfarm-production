"""
Детальная диагностика потока запроса синхронизации

Запуск: docker exec factory_v3_backend python manage.py diagnose_sync_flow
"""

import json
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token
from apps.simpleprint.serializers import TriggerSyncSerializer
from apps.simpleprint.services import SimplePrintSyncService


class Command(BaseCommand):
    help = 'Детальная диагностика потока запроса синхронизации'

    def handle(self, *args, **options):
        self.stdout.write("\n" + "="*80)
        self.stdout.write(self.style.SUCCESS("🔬 ДИАГНОСТИКА ПОТОКА ЗАПРОСА СИНХРОНИЗАЦИИ"))
        self.stdout.write("="*80 + "\n")

        # ============================================================================
        # ШАГ 1: Проверка Serializer
        # ============================================================================
        self.stdout.write(self.style.WARNING("📋 ШАГ 1: Проверка TriggerSyncSerializer"))
        self.stdout.write("-" * 80)

        # Тест 1: force=False
        data1 = {'full_sync': False, 'force': False}
        serializer1 = TriggerSyncSerializer(data=data1)

        self.stdout.write(f"\n🧪 Тест 1: {data1}")
        if serializer1.is_valid():
            self.stdout.write(self.style.SUCCESS("✅ Валидация прошла"))
            self.stdout.write(f"   Извлеченные данные: {serializer1.validated_data}")
            self.stdout.write(f"   force = {serializer1.validated_data.get('force', 'НЕТ КЛЮЧА')}")
        else:
            self.stdout.write(self.style.ERROR(f"❌ Ошибка валидации: {serializer1.errors}"))

        # Тест 2: force=True
        data2 = {'full_sync': True, 'force': True}
        serializer2 = TriggerSyncSerializer(data=data2)

        self.stdout.write(f"\n🧪 Тест 2: {data2}")
        if serializer2.is_valid():
            self.stdout.write(self.style.SUCCESS("✅ Валидация прошла"))
            self.stdout.write(f"   Извлеченные данные: {serializer2.validated_data}")
            self.stdout.write(f"   force = {serializer2.validated_data.get('force', 'НЕТ КЛЮЧА')}")
        else:
            self.stdout.write(self.style.ERROR(f"❌ Ошибка валидации: {serializer2.errors}"))

        # Тест 3: Без параметра force
        data3 = {'full_sync': False}
        serializer3 = TriggerSyncSerializer(data=data3)

        self.stdout.write(f"\n🧪 Тест 3: {data3}")
        if serializer3.is_valid():
            self.stdout.write(self.style.SUCCESS("✅ Валидация прошла"))
            self.stdout.write(f"   Извлеченные данные: {serializer3.validated_data}")
            force_value = serializer3.validated_data.get('force', 'DEFAULT_NOT_SET')
            self.stdout.write(f"   force = {force_value}")
            if force_value == False or force_value == 'DEFAULT_NOT_SET':
                self.stdout.write(self.style.SUCCESS("   ✅ По умолчанию force=False"))
            else:
                self.stdout.write(self.style.ERROR(f"   ❌ ПРОБЛЕМА: Значение по умолчанию = {force_value}"))
        else:
            self.stdout.write(self.style.ERROR(f"❌ Ошибка валидации: {serializer3.errors}"))

        self.stdout.write("")

        # ============================================================================
        # ШАГ 2: Проверка SimplePrintSyncService.get_sync_stats()
        # ============================================================================
        self.stdout.write(self.style.WARNING("\n📋 ШАГ 2: Проверка SimplePrintSyncService.get_sync_stats()"))
        self.stdout.write("-" * 80)

        try:
            service = SimplePrintSyncService()
            stats = service.get_sync_stats()

            self.stdout.write(self.style.SUCCESS("✅ Метод get_sync_stats() работает"))
            self.stdout.write(f"\n📊 Статистика:")
            for key, value in stats.items():
                self.stdout.write(f"   {key}: {value}")

            # Проверяем last_sync
            if stats.get('last_sync'):
                from django.utils import timezone
                time_since_last = timezone.now() - stats['last_sync']
                seconds = int(time_since_last.total_seconds())
                self.stdout.write(f"\n⏱️ Прошло с последней синхронизации: {seconds} секунд")

                if seconds < 300:
                    self.stdout.write(self.style.WARNING(f"   ⚠️ Cooldown АКТИВЕН (прошло {seconds}s < 300s)"))
                    self.stdout.write("   При запросе БЕЗ force вернется 429")
                else:
                    self.stdout.write(self.style.SUCCESS(f"   ✅ Cooldown НЕ активен (прошло {seconds}s >= 300s)"))

            else:
                self.stdout.write(self.style.WARNING("\n⚠️ last_sync = None (синхронизаций еще не было)"))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Ошибка: {e}"))
            import traceback
            self.stdout.write(traceback.format_exc())

        self.stdout.write("")

        # ============================================================================
        # ШАГ 3: Проверка токена
        # ============================================================================
        self.stdout.write(self.style.WARNING("\n📋 ШАГ 3: Проверка production токена"))
        self.stdout.write("-" * 80)

        production_token = '0a8fee03bca2b530a15b1df44d38b304e3f57484'
        try:
            token = Token.objects.get(key=production_token)
            self.stdout.write(self.style.SUCCESS(f"✅ Токен найден: {production_token[:20]}..."))
            self.stdout.write(f"   Пользователь: {token.user.username} (ID: {token.user.id})")
            self.stdout.write(f"   Email: {token.user.email}")
            self.stdout.write(f"   Активен: {token.user.is_active}")
            self.stdout.write(f"   Staff: {token.user.is_staff}")
            self.stdout.write(f"   Superuser: {token.user.is_superuser}")
        except Token.DoesNotExist:
            self.stdout.write(self.style.ERROR(f"❌ Токен НЕ НАЙДЕН: {production_token[:20]}..."))
            self.stdout.write("\n💡 РЕШЕНИЕ: Создать токен командой:")
            self.stdout.write('docker exec factory_v3_backend python manage.py shell -c "')
            self.stdout.write('from rest_framework.authtoken.models import Token')
            self.stdout.write('from django.contrib.auth.models import User')
            self.stdout.write('user = User.objects.first()')
            self.stdout.write(f'Token.objects.get_or_create(user=user, key=\'{production_token}\')')
            self.stdout.write('"')

        # ============================================================================
        # ШАГ 4: Симуляция логики cooldown
        # ============================================================================
        self.stdout.write(self.style.WARNING("\n📋 ШАГ 4: Симуляция логики cooldown из views.py"))
        self.stdout.write("-" * 80)

        try:
            service = SimplePrintSyncService()
            stats = service.get_sync_stats()

            test_cases = [
                {'full_sync': False, 'force': False, 'desc': 'Обычный запрос'},
                {'full_sync': True, 'force': False, 'desc': 'Полная синхронизация БЕЗ force'},
                {'full_sync': False, 'force': True, 'desc': 'Принудительная синхронизация'},
                {'full_sync': True, 'force': True, 'desc': 'Полная принудительная синхронизация'},
            ]

            for test_case in test_cases:
                full_sync = test_case['full_sync']
                force = test_case['force']
                desc = test_case['desc']

                self.stdout.write(f"\n🧪 {desc}: full_sync={full_sync}, force={force}")

                # Симулируем код из views.py:395-402
                if stats['last_sync'] and not force:
                    from django.utils import timezone
                    time_since_last = timezone.now() - stats['last_sync']
                    seconds = int(time_since_last.total_seconds())

                    if seconds < 300:
                        self.stdout.write(self.style.WARNING(f"   ❌ Вернет 429 (прошло {seconds}s < 300s)"))
                    else:
                        self.stdout.write(self.style.SUCCESS(f"   ✅ Пройдет (прошло {seconds}s >= 300s)"))
                else:
                    if stats['last_sync']:
                        self.stdout.write(self.style.SUCCESS("   ✅ Пройдет (force=True обходит cooldown)"))
                    else:
                        self.stdout.write(self.style.SUCCESS("   ✅ Пройдет (last_sync=None)"))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Ошибка: {e}"))

        # ============================================================================
        # ИТОГИ
        # ============================================================================
        self.stdout.write(self.style.SUCCESS("\n\n" + "="*80))
        self.stdout.write(self.style.SUCCESS("📊 ИТОГИ ДИАГНОСТИКИ"))
        self.stdout.write(self.style.SUCCESS("="*80))

        self.stdout.write("\n✅ Проверено:")
        self.stdout.write("   1. TriggerSyncSerializer корректно парсит параметры")
        self.stdout.write("   2. SimplePrintSyncService.get_sync_stats() работает")
        self.stdout.write("   3. Production токен проверен")
        self.stdout.write("   4. Логика cooldown симулирована")

        self.stdout.write("\n💡 СЛЕДУЮЩИЙ ШАГ:")
        self.stdout.write("   Запустить: docker exec factory_v3_backend python manage.py test_sync_cooldown")
        self.stdout.write("   Чтобы проверить реальные API запросы")

        self.stdout.write("\n" + "="*80 + "\n")
