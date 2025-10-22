"""
SimplePrint Celery Tasks

Фоновые задачи для автоматической синхронизации.
"""

import logging
from celery import shared_task
from django.utils import timezone

from .services import SimplePrintSyncService
from .client import SimplePrintAPIError

logger = logging.getLogger(__name__)


@shared_task(name='simpleprint.sync_files')
def sync_simpleprint_files_task(full_sync=False):
    """
    Celery задача для синхронизации файлов из SimplePrint

    Args:
        full_sync: Полная синхронизация с удалением отсутствующих файлов

    Returns:
        dict: Результаты синхронизации
    """
    logger.info(f"Starting SimplePrint sync task (full_sync={full_sync})")

    try:
        service = SimplePrintSyncService()
        sync_log = service.sync_all_files(full_sync=full_sync)

        result = {
            'status': 'success',
            'sync_id': sync_log.id,
            'total_folders': sync_log.total_folders,
            'synced_folders': sync_log.synced_folders,
            'total_files': sync_log.total_files,
            'synced_files': sync_log.synced_files,
            'deleted_files': sync_log.deleted_files,
            'duration': sync_log.get_duration(),
            'finished_at': sync_log.finished_at.isoformat() if sync_log.finished_at else None
        }

        logger.info(f"SimplePrint sync task completed successfully: {result}")
        return result

    except SimplePrintAPIError as e:
        logger.error(f"SimplePrint API error during sync: {e}")
        return {
            'status': 'error',
            'error_type': 'api_error',
            'message': str(e)
        }

    except Exception as e:
        logger.error(f"SimplePrint sync task failed: {e}", exc_info=True)
        return {
            'status': 'error',
            'error_type': 'general_error',
            'message': str(e)
        }


@shared_task(name='simpleprint.scheduled_sync')
def scheduled_sync_task():
    """
    Запланированная задача для регулярной синхронизации

    Эта задача должна быть настроена в Celery Beat для регулярного выполнения.
    Рекомендуемый интервал: каждые 30 минут.
    """
    logger.info("Starting scheduled SimplePrint sync")

    # Проверяем, нужна ли синхронизация
    service = SimplePrintSyncService()
    stats = service.get_sync_stats()

    if stats['last_sync']:
        time_since_last = timezone.now() - stats['last_sync']
        # Если последняя синхронизация была менее 25 минут назад, пропускаем
        if time_since_last.total_seconds() < 1500:  # 25 минут
            logger.info(f"Skipping scheduled sync: last sync was {int(time_since_last.total_seconds())} seconds ago")
            return {
                'status': 'skipped',
                'reason': 'recent_sync',
                'last_sync': stats['last_sync'].isoformat()
            }

    # Запускаем обычную синхронизацию (без full_sync)
    return sync_simpleprint_files_task(full_sync=False)
