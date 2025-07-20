import logging
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from .models import SyncLog
from .tasks import sync_products_task
from .services import SyncService

logger = logging.getLogger(__name__)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def sync_status(request):
    """
    Get current sync status.
    """
    latest_sync = SyncLog.objects.filter(status='pending').first()
    if latest_sync:
        return Response({
            'is_syncing': True,
            'sync_id': latest_sync.id,
            'started_at': latest_sync.started_at,
            'total_products': latest_sync.total_products,
            'synced_products': latest_sync.synced_products,
            'current_article': latest_sync.current_article,
        })
    else:
        latest_completed = SyncLog.objects.exclude(status='pending').first()
        return Response({
            'is_syncing': False,
            'last_sync': latest_completed.started_at if latest_completed else None,
        })

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def sync_history(request):
    """
    Get sync history.
    """
    logs = SyncLog.objects.all()[:10]  # Last 10 syncs
    data = []
    for log in logs:
        data.append({
            'id': log.id,
            'sync_type': log.sync_type,
            'status': log.status,
            'started_at': log.started_at,
            'finished_at': log.finished_at,
            'warehouse_name': log.warehouse_name,
            'total_products': log.total_products,
            'synced_products': log.synced_products,
            'failed_products': log.failed_products,
            'success_rate': log.success_rate,
            'duration': log.duration.total_seconds() if log.duration else None,
        })
    return Response(data)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def sync_warehouses(request):
    """
    Get available warehouses from МойСклад.
    """
    try:
        from .moysklad_client import MoySkladClient
        client = MoySkladClient()
        warehouses = client.get_warehouses()
        return Response(warehouses)
    except Exception as e:
        # Возвращаем детали ошибки для отладки
        return Response({
            'error': str(e),
            'type': type(e).__name__,
            'detail': 'Failed to fetch warehouses from МойСклад API'
        }, status=status.HTTP_503_SERVICE_UNAVAILABLE)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def sync_product_groups(request):
    """
    Get available product groups from МойСклад.
    """
    try:
        from .moysklad_client import MoySkladClient
        client = MoySkladClient()
        groups = client.get_product_groups()
        return Response(groups)
    except Exception as e:
        # Fallback to demo data if API fails
        return Response([
            {
                'id': 'group-1',
                'name': 'Канцелярские товары',
                'pathName': 'Канцелярские товары'
            },
            {
                'id': 'group-2',
                'name': 'Офисная техника',
                'pathName': 'Офисная техника'
            },
            {
                'id': 'group-3',
                'name': 'Расходные материалы',
                'pathName': 'Расходные материалы'
            },
            {
                'id': 'group-4',
                'name': 'Бытовая химия',
                'pathName': 'Бытовая химия'
            }
        ])

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def start_sync(request):
    """
    Start synchronization with МойСклад.
    """
    warehouse_id = request.data.get('warehouse_id')
    excluded_groups = request.data.get('excluded_groups', [])
    sync_images = request.data.get('sync_images', True)  # По умолчанию включено
    
    if not warehouse_id:
        return Response(
            {'error': 'warehouse_id is required'}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Check if sync is already running
    running_sync = SyncLog.objects.filter(status='pending').first()
    if running_sync:
        return Response(
            {'error': 'Sync is already running', 'sync_id': running_sync.id},
            status=status.HTTP_409_CONFLICT
        )
    
    try:
        # For development, run sync synchronously if DEBUG=True
        from django.conf import settings
        if settings.DEBUG:
            sync_service = SyncService()
            sync_log = sync_service.sync_products(
                warehouse_id=warehouse_id,
                excluded_groups=excluded_groups,
                sync_type='manual',
                sync_images=sync_images
            )
            return Response({
                'message': 'Sync completed',
                'sync_id': sync_log.id,
                'status': sync_log.status,
                'synced_products': sync_log.synced_products,
                'total_products': sync_log.total_products,
                'failed_products': sync_log.failed_products
            }, status=status.HTTP_200_OK)
        else:
            # Production: use async task
            task = sync_products_task.delay(
                warehouse_id=warehouse_id,
                excluded_groups=excluded_groups,
                sync_type='manual',
                sync_images=sync_images
            )
            return Response({
                'message': 'Sync started',
                'task_id': task.id
            }, status=status.HTTP_202_ACCEPTED)
            
    except Exception as e:
        return Response({
            'error': f'Sync failed: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def download_images(request):
    """
    Download images for products without images.
    """
    limit = request.data.get('limit', 50)  # Увеличили лимит по умолчанию
    
    try:
        from apps.products.models import Product
        
        # Get products without images that were synced from МойСклад
        products_without_images = Product.objects.filter(
            images__isnull=True,
            last_synced_at__isnull=False
        ).distinct().order_by('-last_synced_at')[:limit]  # Сначала недавно синхронизированные
        
        if not products_without_images:
            return Response({
                'message': 'No products without images found',
                'synced_products': 0,
                'total_images': 0
            })
        
        sync_service = SyncService()
        total_synced = 0
        synced_products = 0
        
        logger.info(f"Starting bulk image download for {len(products_without_images)} products")
        
        for i, product in enumerate(products_without_images, 1):
            try:
                synced_count = sync_service.sync_product_images(product)
                if synced_count > 0:
                    synced_products += 1
                total_synced += synced_count
                
                # Log progress every 10 products
                if i % 10 == 0:
                    logger.info(f"Processed {i}/{len(products_without_images)} products, downloaded {total_synced} images")
                    
            except Exception as e:
                logger.warning(f"Failed to sync images for product {product.article}: {str(e)}")
                continue
        
        logger.info(f"Bulk image download completed: {total_synced} images for {synced_products} products")
        
        return Response({
            'message': f'Downloaded images for {synced_products} products',
            'synced_products': synced_products,
            'total_images': total_synced,
            'processed_products': len(products_without_images),
            'remaining_without_images': Product.objects.filter(
                images__isnull=True,
                last_synced_at__isnull=False
            ).distinct().count()
        })
        
    except Exception as e:
        logger.error(f"Bulk image download failed: {str(e)}")
        return Response({
            'error': f'Image download failed: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def test_moysklad_data(request):
    """
    Test endpoint to get raw data from МойСклад for debugging.
    """
    warehouse_id = request.data.get('warehouse_id')
    group_name = request.data.get('group_name')
    
    if not warehouse_id:
        return Response({
            'error': 'warehouse_id is required'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        from .moysklad_client import MoySkladClient
        client = MoySkladClient()
        
        # Get product groups to find the target group
        groups = client.get_product_groups()
        target_group = None
        if group_name:
            target_group = next((g for g in groups if g['name'] == group_name), None)
        
        # Get all products with stock info
        excluded_groups = []
        if target_group:
            # Exclude all groups except the target one
            excluded_groups = [g['id'] for g in groups if g['id'] != target_group['id']]
        
        products = client.get_all_products_with_stock(warehouse_id, excluded_groups)
        
        # Filter by group if specified
        if target_group:
            filtered_products = []
            for product in products:
                folder = product.get('folder')
                if folder and folder.get('meta', {}).get('href'):
                    folder_id = folder['meta']['href'].split('/')[-1]
                    if folder_id == target_group['id']:
                        filtered_products.append(product)
            products = filtered_products
        
        return Response({
            'warehouse_id': warehouse_id,
            'group_name': group_name,
            'target_group': target_group,
            'total_products': len(products),
            'products': products[:20],  # Limit to first 20 for performance
            'all_groups': groups
        })
        
    except Exception as e:
        logger.error(f"Test МойСклад data failed: {str(e)}")
        return Response({
            'error': f'Failed to get МойСклад data: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def download_specific_images(request):
    """
    Download images for specific products by articles.
    """
    articles = request.data.get('articles', [])
    
    if not articles:
        return Response({
            'error': 'No articles provided'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        from apps.products.models import Product
        
        # Find products by articles
        products = Product.objects.filter(article__in=articles)
        found_articles = list(products.values_list('article', flat=True))
        missing_articles = [art for art in articles if art not in found_articles]
        
        if missing_articles:
            logger.warning(f"Products not found for articles: {missing_articles}")
        
        sync_service = SyncService()
        total_synced = 0
        synced_products = 0
        results = []
        
        logger.info(f"Starting specific image download for {len(products)} products")
        
        for product in products:
            try:
                synced_count = sync_service.sync_product_images(product)
                if synced_count > 0:
                    synced_products += 1
                total_synced += synced_count
                
                results.append({
                    'article': product.article,
                    'name': product.name[:50],
                    'synced_images': synced_count,
                    'success': True
                })
                
                logger.info(f"Downloaded {synced_count} images for {product.article}")
                
            except Exception as e:
                logger.warning(f"Failed to sync images for product {product.article}: {str(e)}")
                results.append({
                    'article': product.article,
                    'name': product.name[:50],
                    'synced_images': 0,
                    'success': False,
                    'error': str(e)
                })
                continue
        
        return Response({
            'message': f'Downloaded images for {synced_products} products',
            'synced_products': synced_products,
            'total_images': total_synced,
            'requested_articles': len(articles),
            'found_articles': len(found_articles),
            'missing_articles': missing_articles,
            'results': results
        })
        
    except Exception as e:
        logger.error(f"Specific image download failed: {str(e)}")
        return Response({
            'error': f'Image download failed: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
