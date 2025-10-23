"""
SimplePrint Celery Tasks

Асинхронные задачи для синхронизации SimplePrint
"""

import logging
from celery import shared_task
from .services import SimplePrintSyncService

logger = logging.getLogger(__name__)


@shared_task(bind=True, time_limit=3600)  # 1 час максимум
def sync_simpleprint_task(self, full_sync=False):
    """
    Асинхронная задача синхронизации SimplePrint
    
    Args:
        full_sync: Полная синхронизация с удалением
        
    Returns:
        ID синхронизации
    """
    logger.info(f"Starting SimplePrint sync task (full_sync={full_sync})")
    
    try:
        service = SimplePrintSyncService()
        sync_log = service.sync_all_files(full_sync=full_sync)
        
        logger.info(f"SimplePrint sync completed: {sync_log.id}")
        return {
            'sync_id': sync_log.id,
            'status': sync_log.status,
            'total_files': sync_log.total_files,
            'synced_files': sync_log.synced_files,
        }
        
    except Exception as e:
        logger.error(f"SimplePrint sync failed: {e}", exc_info=True)
        raise
