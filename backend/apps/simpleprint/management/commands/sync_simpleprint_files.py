"""
Management команда для синхронизации файлов из SimplePrint
"""

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from apps.simpleprint.services import SimplePrintSyncService
from apps.simpleprint.client import SimplePrintAPIError


class Command(BaseCommand):
    help = 'Синхронизировать файлы и папки из SimplePrint API'

    def add_arguments(self, parser):
        """Добавить аргументы команды"""
        parser.add_argument(
            '--full',
            action='store_true',
            help='Полная синхронизация с удалением отсутствующих файлов',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Принудительная синхронизация (игнорировать недавние синхронизации)',
        )

    def handle(self, *args, **options):
        """Выполнить команду"""
        full_sync = options['full']
        force = options['force']

        self.stdout.write(self.style.NOTICE('=' * 70))
        self.stdout.write(self.style.NOTICE('SimplePrint Files Synchronization'))
        self.stdout.write(self.style.NOTICE('=' * 70))

        # Проверяем последнюю синхронизацию
        service = SimplePrintSyncService()
        stats = service.get_sync_stats()

        if stats['last_sync'] and not force:
            time_since_last = timezone.now() - stats['last_sync']
            if time_since_last.total_seconds() < 300:  # 5 минут
                self.stdout.write(
                    self.style.WARNING(
                        f'Последняя синхронизация была {int(time_since_last.total_seconds())} секунд назад. '
                        f'Используйте --force для принудительной синхронизации.'
                    )
                )
                return

        # Выводим текущую статистику
        self.stdout.write('')
        self.stdout.write(self.style.NOTICE('Текущая статистика:'))
        self.stdout.write(f'  Папок в БД: {stats["total_folders"]}')
        self.stdout.write(f'  Файлов в БД: {stats["total_files"]}')
        if stats['last_sync']:
            self.stdout.write(f'  Последняя синхронизация: {stats["last_sync"]}')
            if stats['last_sync_duration']:
                self.stdout.write(f'  Длительность: {stats["last_sync_duration"]:.1f} секунд')

        self.stdout.write('')
        self.stdout.write(self.style.NOTICE('Параметры синхронизации:'))
        self.stdout.write(f'  Полная синхронизация: {"Да" if full_sync else "Нет"}')
        self.stdout.write(f'  Принудительная: {"Да" if force else "Нет"}')
        self.stdout.write('')

        # Запускаем синхронизацию
        try:
            self.stdout.write(self.style.NOTICE('Запуск синхронизации...'))
            start_time = timezone.now()

            sync_log = service.sync_all_files(full_sync=full_sync)

            end_time = timezone.now()
            duration = (end_time - start_time).total_seconds()

            # Выводим результаты
            self.stdout.write('')
            self.stdout.write(self.style.SUCCESS('✓ Синхронизация завершена успешно!'))
            self.stdout.write('')
            self.stdout.write(self.style.NOTICE('Результаты:'))
            self.stdout.write(f'  Папок найдено: {sync_log.total_folders}')
            self.stdout.write(f'  Папок синхронизировано: {sync_log.synced_folders}')
            self.stdout.write(f'  Файлов найдено: {sync_log.total_files}')
            self.stdout.write(f'  Файлов синхронизировано: {sync_log.synced_files}')
            if full_sync:
                self.stdout.write(f'  Файлов удалено: {sync_log.deleted_files}')
            self.stdout.write(f'  Длительность: {duration:.1f} секунд')
            self.stdout.write('')

        except SimplePrintAPIError as e:
            self.stdout.write('')
            self.stdout.write(self.style.ERROR(f'✗ Ошибка API SimplePrint: {e}'))
            raise CommandError(f'Synchronization failed: {e}')

        except Exception as e:
            self.stdout.write('')
            self.stdout.write(self.style.ERROR(f'✗ Ошибка синхронизации: {e}'))
            raise CommandError(f'Synchronization failed: {e}')

        finally:
            self.stdout.write(self.style.NOTICE('=' * 70))
