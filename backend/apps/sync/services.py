"""
Synchronization services for PrintFarm production system.
"""
import logging
from datetime import datetime, timedelta
from decimal import Decimal
from typing import List, Dict, Optional, Tuple
from PIL import Image
from io import BytesIO

from django.core.files.base import ContentFile
from django.db import transaction
from django.utils import timezone

from apps.products.models import Product, ProductImage
from .models import SyncLog
from .moysklad_client import MoySkladClient
from apps.core.exceptions import SyncException

logger = logging.getLogger(__name__)

class SyncService:
    """
    Service for synchronizing data with МойСклад.
    """
    
    def __init__(self):
        self.client = MoySkladClient()
    
    def sync_products(self, warehouse_id: str, excluded_groups: List[str] = None, sync_type: str = 'manual', sync_images: bool = True) -> SyncLog:
        """
        Main method to sync products from МойСклад.
        """
        # Get warehouse info
        warehouses = self.client.get_warehouses()
        warehouse = next((w for w in warehouses if w['id'] == warehouse_id), None)
        if not warehouse:
            raise SyncException(f"Warehouse with ID {warehouse_id} not found")
        
        # Create sync log
        sync_log = SyncLog.objects.create(
            sync_type=sync_type,
            warehouse_id=warehouse_id,
            warehouse_name=warehouse.get('name', 'Unknown'),
            excluded_groups=excluded_groups or []
        )
        
        try:
            with transaction.atomic():
                # Get ALL products including those with zero stock
                stock_data = self.client.get_all_products_with_stock(warehouse_id, excluded_groups)
                
                # Get turnover report (last 2 months)
                date_to = timezone.now()
                date_from = date_to - timedelta(days=60)
                turnover_data = self.client.get_turnover_report(warehouse_id, date_from, date_to)
                
                # Clear existing products if we have excluded groups to ensure clean filtering
                if excluded_groups:
                    logger.info(f"Clearing existing products due to group filtering")
                    Product.objects.all().delete()
                
                # Process data
                sync_result = self._process_sync_data(stock_data, turnover_data, sync_log)
                
                # Update sync log first
                sync_log.total_products = sync_result['total']
                sync_log.synced_products = sync_result['synced']
                sync_log.failed_products = sync_result['failed']
                sync_log.status = 'success' if sync_result['failed'] == 0 else 'partial'
                sync_log.finished_at = timezone.now()
                sync_log.save()
                
                # Sync images asynchronously if requested (increased limit)
                if sync_images and sync_result['synced_products']:
                    logger.info(f"Starting image synchronization for up to 100 products")
                    # Limit to 100 products to balance performance and completeness
                    limited_products = sync_result['synced_products'][:100]
                    images_synced = self._sync_images_for_products(limited_products, sync_log)
                    logger.info(f"Image synchronization completed: {images_synced} images downloaded for {len(limited_products)} products")
                
        except Exception as e:
            sync_log.status = 'failed'
            sync_log.error_details = str(e)
            sync_log.finished_at = timezone.now()
            sync_log.save()
            logger.error(f"Sync failed: {str(e)}")
            raise
        
        return sync_log
    
    def _process_sync_data(self, stock_data: List[Dict], turnover_data: List[Dict], sync_log: SyncLog) -> Dict[str, int]:
        """
        Process stock and turnover data and update products.
        """
        # Build turnover lookup dict by product article for better matching
        turnover_dict = {}
        for item in turnover_data:
            assortment = item.get('assortment', {})
            article = assortment.get('article', '')
            if article:
                turnover_dict[article] = item
        
        logger.info(f"Built turnover lookup for {len(turnover_dict)} products by article")
        
        # Build product groups lookup for getting group names
        groups_dict = {}
        try:
            groups = self.client.get_product_groups()
            for group in groups:
                groups_dict[group['id']] = group['name']
            logger.info(f"Built groups lookup for {len(groups_dict)} groups")
        except Exception as e:
            logger.warning(f"Failed to load product groups for names: {str(e)}")
            groups_dict = {}
        
        total = len(stock_data)
        synced = 0
        failed = 0
        synced_products = []  # Keep track of synced products for image sync
        
        for item in stock_data:
            try:
                # Extract product data from new API format
                meta = item.get('meta', {})
                
                if meta.get('type') != 'product':
                    continue
                
                # Проверяем статус архивности
                if item.get('archived', False):
                    logger.debug(f"Skipping archived product: {item.get('name', 'Unknown')}")
                    continue
                
                product_href = meta.get('href', '')
                product_id = product_href.split('/')[-1].split('?')[0] if product_href else ''
                if not product_id:
                    failed += 1
                    continue
                
                # Get or create product
                product, created = Product.objects.get_or_create(
                    moysklad_id=product_id,
                    defaults={
                        'article': item.get('article', ''),
                        'name': item.get('name', ''),
                        'description': '',
                    }
                )
                
                # Update product data from stock report format
                product.article = item.get('article', '')
                product.name = item.get('name', '')
                product.current_stock = Decimal(str(item.get('stock', 0)))
                
                # Update reserved stock if available
                product.reserved_stock = Decimal(str(item.get('reserve', 0)))
                
                # Update product group from folder
                if 'folder' in item:
                    folder = item['folder']
                    folder_href = folder.get('meta', {}).get('href', '')
                    if folder_href:
                        group_id = folder_href.split('/')[-1]
                        product.product_group_id = group_id
                        # Get group name from lookup dict
                        product.product_group_name = groups_dict.get(group_id, '')
                
                # Update sales data from turnover (if available) - match by article
                article = item.get('article', '')
                if article and article in turnover_dict:
                    turnover_item = turnover_dict[article]
                    # Get sales quantity from outcome field
                    outcome_data = turnover_item.get('outcome', {})
                    if isinstance(outcome_data, dict):
                        sales_qty = outcome_data.get('quantity', 0)
                    else:
                        sales_qty = outcome_data
                    
                    product.sales_last_2_months = Decimal(str(sales_qty))
                    
                    # Calculate average daily consumption
                    if product.sales_last_2_months > 0:
                        product.average_daily_consumption = product.sales_last_2_months / Decimal('60')
                    else:
                        product.average_daily_consumption = Decimal('0')
                        
                    logger.debug(f"  Found turnover for {article}: sales={product.sales_last_2_months}, daily={product.average_daily_consumption}")
                else:
                    # No turnover data, set to 0
                    product.sales_last_2_months = Decimal('0')
                    product.average_daily_consumption = Decimal('0')
                    if article:
                        logger.debug(f"  No turnover data for {article}")
                
                # Получение цвета товара из атрибутов МойСклад
                try:
                    # Извлекаем цвет из атрибутов, если они есть в данных
                    attributes = item.get('attributes', [])
                    if attributes:
                        color = self.client.extract_color_from_attributes(attributes)
                        product.color = color
                        logger.debug(f"  Обновлен цвет для {article}: {color}")
                    else:
                        # Если атрибуты не включены в stock_data, делаем отдельный запрос
                        # TODO: Оптимизация - получать цвета батчами для производительности
                        if product_id:
                            product_details = self.client.get_product_details(product_id)
                            color = product_details.get('color', '')
                            product.color = color
                            if color:
                                logger.debug(f"  Загружен цвет для {article}: {color}")
                except Exception as e:
                    logger.warning(f"Ошибка при загрузке цвета для товара {article}: {str(e)}")
                    # Не прерываем синхронизацию из-за ошибки цвета
                    product.color = ''
                
                product.last_synced_at = timezone.now()
                product.save()  # This will trigger calculation of derived fields
                
                synced += 1
                synced_products.append(product)  # Add to list for image sync
                
                # Update sync log progress periodically
                if synced % 100 == 0:
                    sync_log.synced_products = synced
                    sync_log.save()
                
            except Exception as e:
                logger.error(f"Failed to process product {item}: {str(e)}")
                failed += 1
                continue
        
        return {
            'total': total,
            'synced': synced,
            'failed': failed,
            'synced_products': synced_products  # Include synced products for image sync
        }
    
    def sync_product_images(self, product: Product) -> int:
        """
        Sync images for a specific product.
        """
        try:
            images_data = self.client.get_product_images(product.moysklad_id)
            synced_count = 0
            
            for image_data in images_data:
                download_href = image_data.get('meta', {}).get('downloadHref')
                if not download_href:
                    continue
                
                # Check if image already exists
                existing_image = ProductImage.objects.filter(
                    product=product,
                    moysklad_url=download_href
                ).first()
                
                if existing_image:
                    continue
                
                # Download image
                image_content = self.client.download_image(download_href)
                if not image_content:
                    continue
                
                # Create ProductImage
                image_name = f"{product.article}_{image_data.get('filename', 'image')}"
                
                product_image = ProductImage.objects.create(
                    product=product,
                    moysklad_url=download_href,
                    is_main=synced_count == 0  # First image is main
                )
                
                # Save original image
                product_image.image.save(
                    image_name,
                    ContentFile(image_content),
                    save=False
                )
                
                # Create thumbnail
                try:
                    thumbnail_content = self._create_thumbnail(image_content)
                    if thumbnail_content:
                        product_image.thumbnail.save(
                            f"thumb_{image_name}",
                            ContentFile(thumbnail_content),
                            save=False
                        )
                except Exception as e:
                    logger.warning(f"Failed to create thumbnail for {image_name}: {str(e)}")
                
                product_image.save()
                synced_count += 1
            
            return synced_count
            
        except Exception as e:
            logger.error(f"Failed to sync images for product {product.article}: {str(e)}")
            return 0
    
    def _sync_images_for_products(self, products: List[Product], sync_log: SyncLog, limit: int = 100) -> int:
        """
        Sync images for a list of products with rate limiting.
        """
        total_images_synced = 0
        products_to_process = products[:limit]  # Limit to avoid overloading
        
        logger.info(f"Starting image sync for {len(products_to_process)} products")
        
        for i, product in enumerate(products_to_process, 1):
            try:
                # Skip if product already has images
                if product.images.exists():
                    continue
                
                logger.debug(f"Syncing images for product {i}/{len(products_to_process)}: {product.article}")
                
                synced_count = self.sync_product_images(product)
                total_images_synced += synced_count
                
                if synced_count > 0:
                    logger.debug(f"  ✓ Downloaded {synced_count} images for {product.article}")
                
                # Update sync log progress every 10 products
                if i % 10 == 0:
                    logger.info(f"Image sync progress: {i}/{len(products_to_process)} products processed")
                
            except Exception as e:
                logger.warning(f"Failed to sync images for product {product.article}: {str(e)}")
                continue
        
        logger.info(f"Image sync completed: {total_images_synced} images downloaded for {len(products_to_process)} products")
        return total_images_synced
    
    def _create_thumbnail(self, image_content: bytes, size: Tuple[int, int] = (150, 150)) -> Optional[bytes]:
        """
        Create thumbnail from image content.
        """
        try:
            image = Image.open(BytesIO(image_content))
            image.thumbnail(size, Image.Resampling.LANCZOS)
            
            # Convert to RGB if necessary
            if image.mode in ('RGBA', 'LA', 'P'):
                background = Image.new('RGB', image.size, (255, 255, 255))
                background.paste(image, mask=image.split()[-1] if image.mode == 'RGBA' else None)
                image = background
            
            # Save as JPEG
            output = BytesIO()
            image.save(output, format='JPEG', quality=85, optimize=True)
            return output.getvalue()
            
        except Exception as e:
            logger.error(f"Failed to create thumbnail: {str(e)}")
            return None
    
    def test_connection(self) -> bool:
        """
        Test connection to МойСклад API.
        """
        return self.client.test_connection()