from rest_framework import generics, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q, Count, Sum, Value
from django.db.models.functions import Lower
from .models import Product
from .serializers import ProductListSerializer, ProductDetailSerializer, ProductStatsSerializer
# from .services import ProductionService  # TODO: Create ProductionService
from apps.sync.models import ProductionList
from apps.sync.services import SyncService

class ProductListView(generics.ListAPIView):
    """
    List view for products with filtering and search.
    Supports include_reserve parameter for calculating effective stock.
    """
    serializer_class = ProductListSerializer
    # # permission_classes = [IsAuthenticated]  # Временно отключено  # Временно отключено для разработки
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['product_type', 'product_group_id']
    
    def get_serializer_context(self):
        """Pass include_reserve flag to serializer context."""
        context = super().get_serializer_context()
        include_reserve = self.request.query_params.get('include_reserve', 'false').lower() == 'true'
        context['include_reserve'] = include_reserve
        return context
    
    def get_queryset(self):
        queryset = Product.objects.select_related().prefetch_related('images')
        
        # Search functionality - universal case-insensitive search
        search = self.request.query_params.get('search', None)
        if search:
            from django.db import connection
            
            if connection.vendor == 'sqlite':
                # Для SQLite используем комбинированный подход
                # 1. Обычный icontains для латиницы
                # 2. Ручной поиск для кириллицы
                
                # Сначала пробуем обычный icontains
                base_queryset = queryset.filter(
                    Q(article__icontains=search) | 
                    Q(name__icontains=search) |
                    Q(description__icontains=search)
                )
                
                # Если поиск содержит кириллицу, добавляем дополнительную логику
                if any('\u0400' <= char <= '\u04FF' for char in search):
                    # Получаем все товары для фильтрации в Python
                    all_products = list(queryset.values('id', 'article', 'name', 'description'))
                    search_lower = search.lower()
                    
                    matching_ids = []
                    for product in all_products:
                        # Проверяем каждое поле на регистронезависимое вхождение
                        fields_to_check = [
                            (product.get('article') or '').lower(),
                            (product.get('name') or '').lower(),
                            (product.get('description') or '').lower()
                        ]
                        
                        if any(search_lower in field for field in fields_to_check):
                            matching_ids.append(product['id'])
                    
                    # Объединяем результаты
                    if matching_ids:
                        cyrillic_queryset = queryset.filter(id__in=matching_ids)
                        # Объединяем с base_queryset и убираем дубликаты
                        queryset = (base_queryset | cyrillic_queryset).distinct()
                    else:
                        queryset = base_queryset
                else:
                    queryset = base_queryset
            else:
                # Для PostgreSQL и других БД используем стандартный icontains
                queryset = queryset.filter(
                    Q(article__icontains=search) | 
                    Q(name__icontains=search) |
                    Q(description__icontains=search)
                )
        
        # Stock filters
        min_stock = self.request.query_params.get('min_stock', None)
        max_stock = self.request.query_params.get('max_stock', None)
        if min_stock:
            queryset = queryset.filter(current_stock__gte=min_stock)
        if max_stock:
            queryset = queryset.filter(current_stock__lte=max_stock)
        
        # Priority filters
        min_priority = self.request.query_params.get('min_priority', None)
        if min_priority:
            queryset = queryset.filter(production_priority__gte=min_priority)
        
        # Production needed filter
        production_needed = self.request.query_params.get('production_needed', None)
        if production_needed == 'true':
            queryset = queryset.filter(production_needed__gt=0)
        
        # Filter by product group name
        product_group_name = self.request.query_params.get('product_group_name', None)
        if product_group_name:
            queryset = queryset.filter(product_group_name__icontains=product_group_name)
        
        # Filter products with images
        has_images = self.request.query_params.get('has_images', None)
        if has_images == 'true':
            queryset = queryset.filter(images__isnull=False).distinct()
        elif has_images == 'false':
            queryset = queryset.filter(images__isnull=True)
        
        # Sorting
        ordering = self.request.query_params.get('ordering', None)
        if ordering:
            # Допустимые поля для сортировки
            allowed_fields = [
                'article', 'name', 'product_type', 'current_stock', 
                'sales_last_2_months', 'average_daily_consumption', 
                'days_of_stock', 'production_needed', 'production_priority'
            ]
            
            # Убираем знак минуса для проверки поля
            field_name = ordering.lstrip('-')
            
            if field_name in allowed_fields:
                queryset = queryset.order_by(ordering)
            else:
                # Если поле не разрешено, используем сортировку по умолчанию
                queryset = queryset.order_by('-production_priority', 'article')
        else:
            # Сортировка по умолчанию
            queryset = queryset.order_by('-production_priority', 'article')
        
        return queryset

class ProductDetailView(generics.RetrieveAPIView):
    """
    Detail view for a single product.
    """
    queryset = Product.objects.prefetch_related('images')
    serializer_class = ProductDetailSerializer
    # permission_classes = [IsAuthenticated]  # Временно отключено

@api_view(['GET'])
# @permission_classes([IsAuthenticated])  # Временно отключено
def product_stats(request):
    """
    Get product statistics.
    """
    stats = {
        'total_products': Product.objects.count(),
        'new_products': Product.objects.filter(product_type='new').count(),
        'old_products': Product.objects.filter(product_type='old').count(),
        'critical_products': Product.objects.filter(product_type='critical').count(),
        'production_needed_items': Product.objects.filter(production_needed__gt=0).count(),
        'total_production_units': Product.objects.aggregate(
            total=Sum('production_needed')
        )['total'] or 0
    }
    
    serializer = ProductStatsSerializer(stats)
    return Response(serializer.data)

@api_view(['POST'])
# @permission_classes([IsAuthenticated])  # Временно отключено
def calculate_production_list(request):
    """
    Calculate new production list.
    """
    min_priority = request.data.get('min_priority', 20)
    apply_coefficients = request.data.get('apply_coefficients', True)
    
    try:
        production_service = ProductionService()
        production_list = production_service.calculate_production_list(
            min_priority=min_priority,
            apply_coefficients=apply_coefficients
        )
        
        return Response({
            'message': 'Production list calculated successfully',
            'production_list_id': production_list.id,
            'total_items': production_list.total_items,
            'total_units': float(production_list.total_units)
        }, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        return Response({
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
# @permission_classes([IsAuthenticated])  # Временно отключено
def get_production_list(request, list_id=None):
    """
    Get production list data.
    """
    try:
        if list_id:
            production_list = ProductionList.objects.get(id=list_id)
        else:
            # Get latest production list
            production_list = ProductionList.objects.first()
            if not production_list:
                return Response({
                    'error': 'No production lists found'
                }, status=status.HTTP_404_NOT_FOUND)
        
        production_service = ProductionService()
        data = production_service.get_production_list_data(production_list)
        
        return Response(data)
        
    except ProductionList.DoesNotExist:
        return Response({
            'error': 'Production list not found'
        }, status=status.HTTP_404_NOT_FOUND)

@api_view(['GET'])
# @permission_classes([IsAuthenticated])  # Временно отключено
def production_stats(request):
    """
    Get production statistics.
    """
    production_service = ProductionService()
    stats = production_service.get_production_stats()
    return Response(stats)

@api_view(['POST'])
# @permission_classes([IsAuthenticated])  # Временно отключено
def recalculate_production(request):
    """
    Recalculate production needs for all products.
    """
    try:
        production_service = ProductionService()
        result = production_service.recalculate_all_products()
        
        return Response({
            'message': 'Production recalculation completed',
            **result
        })
        
    except Exception as e:
        return Response({
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
# @permission_classes([IsAuthenticated])  # Временно отключено
def export_production_list_view(request, list_id=None):
    """
    Export production list to Excel.
    """
    from apps.reports.exporters import ProductionListExporter
    
    try:
        if list_id:
            production_list = ProductionList.objects.get(id=list_id)
        else:
            production_list = ProductionList.objects.first()
            if not production_list:
                return Response({
                    'error': 'No production lists found'
                }, status=status.HTTP_404_NOT_FOUND)
        
        exporter = ProductionListExporter()
        return exporter.export_production_list(production_list)
        
    except ProductionList.DoesNotExist:
        return Response({
            'error': 'Production list not found'
        }, status=status.HTTP_404_NOT_FOUND)

@api_view(['POST'])
# @permission_classes([IsAuthenticated])  # Временно отключено
def sync_product_images_view(request, pk):
    """
    Sync images for specific product.
    """
    try:
        product = Product.objects.get(pk=pk)
        sync_service = SyncService()
        
        synced_count = sync_service.sync_product_images(product)
        
        return Response({
            'message': f'Synced {synced_count} images for product {product.article}',
            'synced_images': synced_count,
            'product_id': product.id
        })
        
    except Product.DoesNotExist:
        return Response({
            'error': 'Product not found'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
