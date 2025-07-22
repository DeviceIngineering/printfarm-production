from django.utils import timezone
from django_celery_beat.models import PeriodicTask, IntervalSchedule
from apps.sync.tasks import scheduled_sync_task
from .models import SyncScheduleSettings, SystemInfo, GeneralSettings
import json


class SettingsService:
    """Сервис для управления настройками системы"""
    
    @staticmethod
    def get_system_summary():
        """Получить сводную информацию о системе"""
        from apps.products.models import Product
        from apps.sync.models import SyncLog
        
        # Системная информация
        system_info = SystemInfo.get_instance()
        sync_settings = SyncScheduleSettings.get_instance()
        general_settings = GeneralSettings.get_instance()
        
        # Статистика продуктов
        total_products = Product.objects.count()
        
        # Информация о последней синхронизации
        last_sync = SyncLog.objects.order_by('-started_at').first()
        last_sync_info = {
            'date': last_sync.started_at if last_sync else None,
            'status': last_sync.status if last_sync else 'never',
            'total_products': last_sync.total_products if last_sync else 0,
            'synced_products': last_sync.synced_products if last_sync else 0,
        }
        
        # Статус системы
        system_status = {
            'sync_enabled': sync_settings.sync_enabled,
            'next_sync': sync_settings.next_sync_time,
            'database_healthy': True,  # TODO: добавить проверки
            'api_healthy': True,  # TODO: добавить проверки
        }
        
        return {
            'system_info': system_info,
            'sync_settings': sync_settings,
            'general_settings': general_settings,
            'total_products': total_products,
            'last_sync_info': last_sync_info,
            'system_status': system_status,
        }
    
    @staticmethod
    def update_sync_schedule(settings: SyncScheduleSettings):
        """Обновить расписание синхронизации в Celery Beat"""
        from django.utils import timezone
        
        task_name = 'sync-moysklad-scheduled'
        
        try:
            # Удаляем существующую задачу
            PeriodicTask.objects.filter(name=task_name).delete()
            
            if settings.sync_enabled:
                # Создаем или получаем интервал
                schedule, created = IntervalSchedule.objects.get_or_create(
                    every=settings.sync_interval_minutes,
                    period=IntervalSchedule.MINUTES,
                )
                
                # Создаем новую задачу
                PeriodicTask.objects.create(
                    name=task_name,
                    task='apps.sync.tasks.scheduled_sync_task',
                    interval=schedule,
                    kwargs=json.dumps({
                        'warehouse_id': settings.warehouse_id,
                        'excluded_groups': settings.excluded_group_ids,
                    }),
                    enabled=True,
                )
                
                # Устанавливаем время создания расписания
                settings.schedule_created_at = timezone.now()
                settings.save()
                
                return {'success': True, 'message': f'Синхронизация настроена каждые {settings.sync_interval_display}'}
            else:
                # При отключении синхронизации сбрасываем время создания расписания
                settings.schedule_created_at = None
                settings.save()
                return {'success': True, 'message': 'Автоматическая синхронизация отключена'}
                
        except Exception as e:
            return {'success': False, 'message': f'Ошибка настройки расписания: {str(e)}'}
    
    @staticmethod
    def get_sync_schedule_status():
        """Получить статус расписания синхронизации"""
        task_name = 'sync-moysklad-scheduled'
        
        try:
            task = PeriodicTask.objects.get(name=task_name)
            return {
                'enabled': task.enabled,
                'interval': f"каждые {task.interval.every} {task.interval.period}",
                'last_run': task.last_run_at,
                'next_run': None,  # Celery Beat не предоставляет эту информацию напрямую
                'total_runs': task.total_run_count,
            }
        except PeriodicTask.DoesNotExist:
            return {
                'enabled': False,
                'interval': 'не настроено',
                'last_run': None,
                'next_run': None,
                'total_runs': 0,
            }
    
    @staticmethod
    def test_sync_connection():
        """Тестировать подключение к МойСклад"""
        from apps.sync.services import SyncService
        
        try:
            sync_service = SyncService()
            # Тестируем получение складов
            warehouses = sync_service.client.get_warehouses()
            
            return {
                'success': True,
                'message': f'Подключение успешно. Найдено складов: {len(warehouses)}',
                'data': {
                    'warehouses_count': len(warehouses),
                    'connection_time': timezone.now(),
                }
            }
        except Exception as e:
            return {
                'success': False,
                'message': f'Ошибка подключения: {str(e)}',
                'data': None
            }
    
    @staticmethod
    def trigger_manual_sync(warehouse_id=None, excluded_groups=None):
        """Запустить ручную синхронизацию"""
        from apps.sync.tasks import sync_products_task
        
        settings = SyncScheduleSettings.get_instance()
        
        # Используем настройки по умолчанию если не переданы параметры
        if not warehouse_id:
            warehouse_id = settings.warehouse_id
        
        if excluded_groups is None:
            excluded_groups = settings.excluded_group_ids
        
        try:
            # Запускаем задачу асинхронно
            task = sync_products_task.delay(
                warehouse_id=warehouse_id,
                excluded_groups=excluded_groups,
                sync_type='manual'
            )
            
            return {
                'success': True,
                'message': 'Синхронизация запущена',
                'task_id': task.id
            }
        except Exception as e:
            return {
                'success': False,
                'message': f'Ошибка запуска синхронизации: {str(e)}',
                'task_id': None
            }


class ScheduleManager:
    """Менеджер для управления расписанием задач"""
    
    @staticmethod
    def create_or_update_sync_schedule(interval_minutes: int, enabled: bool = True):
        """Создать или обновить расписание синхронизации"""
        task_name = 'sync-moysklad-scheduled'
        
        # Удаляем существующие задачи
        PeriodicTask.objects.filter(name=task_name).delete()
        
        if enabled:
            # Создаем интервал
            schedule, _ = IntervalSchedule.objects.get_or_create(
                every=interval_minutes,
                period=IntervalSchedule.MINUTES,
            )
            
            # Создаем задачу
            task = PeriodicTask.objects.create(
                name=task_name,
                task='apps.sync.tasks.scheduled_sync_task',
                interval=schedule,
                enabled=True,
                start_time=timezone.now(),
            )
            
            return task
        
        return None
    
    @staticmethod
    def disable_sync_schedule():
        """Отключить расписание синхронизации"""
        task_name = 'sync-moysklad-scheduled'
        
        try:
            task = PeriodicTask.objects.get(name=task_name)
            task.enabled = False
            task.save()
            return task
        except PeriodicTask.DoesNotExist:
            return None
    
    @staticmethod
    def get_all_scheduled_tasks():
        """Получить все запланированные задачи"""
        return PeriodicTask.objects.all().order_by('name')