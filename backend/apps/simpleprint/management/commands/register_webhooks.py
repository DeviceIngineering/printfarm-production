"""
Management команда для регистрации webhooks в SimplePrint

Usage:
    python manage.py register_webhooks              # Зарегистрировать webhooks
    python manage.py register_webhooks --list       # Показать существующие
    python manage.py register_webhooks --test ID    # Протестировать webhook
"""

from django.core.management.base import BaseCommand
from apps.simpleprint.webhook_manager import SimplePrintWebhookManager


class Command(BaseCommand):
    help = 'Зарегистрировать webhooks в SimplePrint для событий принтеров'

    def add_arguments(self, parser):
        parser.add_argument(
            '--list',
            action='store_true',
            help='Показать существующие webhooks'
        )

        parser.add_argument(
            '--test',
            type=str,
            help='Протестировать webhook по ID'
        )

        parser.add_argument(
            '--delete',
            type=str,
            help='Удалить webhook по ID'
        )

        parser.add_argument(
            '--enable',
            type=str,
            help='Включить webhook по ID'
        )

        parser.add_argument(
            '--disable',
            type=str,
            help=('Выключить webhook по ID')
        )

    def handle(self, *args, **options):
        manager = SimplePrintWebhookManager()

        # Показать список webhooks
        if options['list']:
            self.stdout.write(self.style.SUCCESS('📋 Список зарегистрированных webhooks:'))
            self.stdout.write('')

            webhooks = manager.list_webhooks()

            if not webhooks:
                self.stdout.write(self.style.WARNING('  Webhooks не найдены'))
                self.stdout.write('')
                self.stdout.write('  Запустите: python manage.py register_webhooks')
                return

            for webhook in webhooks:
                self.stdout.write(f"  🔗 ID: {webhook.get('id')}")
                self.stdout.write(f"     URL: {webhook.get('url')}")
                self.stdout.write(f"     Enabled: {'✅ Да' if webhook.get('enabled') else '❌ Нет'}")
                self.stdout.write(f"     Events: {', '.join(webhook.get('events', []))}")
                if webhook.get('description'):
                    self.stdout.write(f"     Description: {webhook.get('description')}")
                self.stdout.write('')

            return

        # Тестировать webhook
        if options['test']:
            webhook_id = options['test']
            self.stdout.write(f'🧪 Тестирование webhook {webhook_id}...')

            result = manager.test_webhook(webhook_id)

            if result.get('status'):
                self.stdout.write(self.style.SUCCESS('✅ Webhook отправлен успешно'))
            else:
                self.stdout.write(self.style.ERROR(f'❌ Ошибка: {result.get("error")}'))

            return

        # Удалить webhook
        if options['delete']:
            webhook_id = options['delete']
            self.stdout.write(f'🗑️  Удаление webhook {webhook_id}...')

            result = manager.delete_webhook(webhook_id)

            if result.get('status'):
                self.stdout.write(self.style.SUCCESS('✅ Webhook удален'))
            else:
                self.stdout.write(self.style.ERROR(f'❌ Ошибка: {result.get("error")}'))

            return

        # Включить webhook
        if options['enable']:
            webhook_id = options['enable']
            self.stdout.write(f'🔄 Включение webhook {webhook_id}...')

            success = manager.enable_webhook(webhook_id, enabled=True)

            if success:
                self.stdout.write(self.style.SUCCESS('✅ Webhook включен'))
            else:
                self.stdout.write(self.style.ERROR('❌ Ошибка включения webhook'))

            return

        # Выключить webhook
        if options['disable']:
            webhook_id = options['disable']
            self.stdout.write(f'🔄 Выключение webhook {webhook_id}...')

            success = manager.enable_webhook(webhook_id, enabled=False)

            if success:
                self.stdout.write(self.style.SUCCESS('✅ Webhook выключен'))
            else:
                self.stdout.write(self.style.ERROR('❌ Ошибка выключения webhook'))

            return

        # Регистрация webhooks (дефолтное действие)
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('🔗 Регистрация webhooks для принтеров...'))
        self.stdout.write('')

        result = manager.register_printer_webhooks()

        if result['status'] == 'created':
            self.stdout.write(self.style.SUCCESS('✅ Webhook успешно зарегистрирован!'))
            self.stdout.write('')
            self.stdout.write(f"  URL: {result['url']}")
            self.stdout.write(f"  Events: {', '.join(result['events'])}")
            self.stdout.write('')
            self.stdout.write('📝 Теперь SimplePrint будет отправлять события на ваш сервер')

        elif result['status'] == 'exists':
            self.stdout.write(self.style.WARNING('⚠️  Webhook уже зарегистрирован'))
            self.stdout.write('')
            self.stdout.write(f"  URL: {result['url']}")
            self.stdout.write('')
            self.stdout.write('  Используйте --list для просмотра всех webhooks')

        else:
            self.stdout.write(self.style.ERROR(f'❌ Ошибка регистрации: {result.get("error")}'))
            self.stdout.write('')
            self.stdout.write('  Проверьте:')
            self.stdout.write('  1. Доступность SimplePrint API')
            self.stdout.write('  2. Корректность API токена')
            self.stdout.write('  3. Доступность webhook URL извне')
