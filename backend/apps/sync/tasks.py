"""
Celery tasks for synchronization with МойСклад.
"""
import logging
from celery import shared_task
from django.conf import settings
from .services import SyncService
from apps.products.models import Product

logger = logging.getLogger(__name__)

@shared_task(bind=True)
def sync_products_task(self, warehouse_id: str, excluded_groups: list = None, sync_type: str = 'manual', sync_images: bool = True):
    """
    Asynchronous task to sync products from МойСклад.
    """
    try:
        sync_service = SyncService()
        sync_log = sync_service.sync_products(
            warehouse_id=warehouse_id,
            excluded_groups=excluded_groups or [],
            sync_type=sync_type,
            sync_images=sync_images
        )
        
        logger.info(f"Sync completed: {sync_log.synced_products}/{sync_log.total_products} products synced")
        return {
            'sync_id': sync_log.id,
            'status': sync_log.status,
            'synced_products': sync_log.synced_products,
            'total_products': sync_log.total_products,
            'failed_products': sync_log.failed_products
        }
        
    except Exception as e:
        logger.error(f"Sync task failed: {str(e)}")
        self.retry(countdown=60, max_retries=3)

@shared_task
def scheduled_sync():
    """
    Scheduled task for automatic daily sync.
    """
    try:
        sync_service = SyncService()
        default_warehouse = settings.MOYSKLAD_CONFIG['default_warehouse_id']
        
        sync_log = sync_service.sync_products(
            warehouse_id=default_warehouse,
            sync_type='scheduled',
            sync_images=True  # Включаем синхронизацию изображений в автоматическом режиме
        )
        
        logger.info(f"Scheduled sync completed: {sync_log.synced_products} products synced")
        return sync_log.id
        
    except Exception as e:
        logger.error(f"Scheduled sync failed: {str(e)}")
        raise

@shared_task(bind=True)
def sync_product_images_task(self, product_id: int):
    """
    Asynchronous task to sync images for a specific product.
    """
    try:
        product = Product.objects.get(id=product_id)
        sync_service = SyncService()
        
        synced_count = sync_service.sync_product_images(product)
        
        logger.info(f"Synced {synced_count} images for product {product.article}")
        return {
            'product_id': product_id,
            'synced_images': synced_count
        }
        
    except Product.DoesNotExist:
        logger.error(f"Product with ID {product_id} not found")
        return {'error': 'Product not found'}
    except Exception as e:
        logger.error(f"Image sync task failed for product {product_id}: {str(e)}")
        self.retry(countdown=30, max_retries=2)

@shared_task
def bulk_sync_images():
    """
    Bulk sync images for products without images.
    """
    try:
        # Get products without images that were synced recently
        products_without_images = Product.objects.filter(
            images__isnull=True,
            last_synced_at__isnull=False
        ).distinct()[:50]  # Limit to 50 to avoid overwhelming the API
        
        total_synced = 0
        for product in products_without_images:
            sync_service = SyncService()
            synced_count = sync_service.sync_product_images(product)
            total_synced += synced_count
        
        logger.info(f"Bulk image sync completed: {total_synced} images synced for {len(products_without_images)} products")
        return {
            'products_processed': len(products_without_images),
            'total_images_synced': total_synced
        }
        
    except Exception as e:
        logger.error(f"Bulk image sync failed: {str(e)}")
        raise