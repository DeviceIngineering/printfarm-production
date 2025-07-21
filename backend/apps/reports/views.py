from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from apps.products.models import Product
from .exporters import ProductsExporter
from .auth import auth_from_query_param

@api_view(['GET'])
# @permission_classes([IsAuthenticated])  # Временно отключено
def reports_list(request):
    """
    Get list of available reports (заглушка).
    """
    return Response([
        {
            'id': 'production_list',
            'name': 'Список на производство',
            'description': 'Основной отчет с приоритизированным списком товаров на производство'
        },
        {
            'id': 'stock_analysis',
            'name': 'Анализ остатков',
            'description': 'Детальный анализ товарных остатков и оборачиваемости'
        },
        {
            'id': 'sales_forecast',
            'name': 'Прогноз продаж',
            'description': 'Прогнозирование потребности на основе исторических данных'
        }
    ])

@api_view(['GET'])
@auth_from_query_param
def export_production_list(request, list_id=None):
    """
    Export production list to Excel (временная заглушка).
    """
    # Временно используем экспорт товаров с фильтрацией по production_needed
    queryset = Product.objects.filter(production_needed__gt=0)
    queryset = queryset.order_by('-production_priority', 'article')
    
    exporter = ProductsExporter()
    return exporter.export_products(queryset)

@api_view(['GET'])
@auth_from_query_param
def export_products(request):
    """
    Export products to Excel.
    """
    # Apply filters from query params
    queryset = Product.objects.all()
    
    product_type = request.query_params.get('product_type')
    if product_type:
        queryset = queryset.filter(product_type=product_type)
    
    production_needed = request.query_params.get('production_needed')
    if production_needed == 'true':
        queryset = queryset.filter(production_needed__gt=0)
    
    min_priority = request.query_params.get('min_priority')
    if min_priority:
        queryset = queryset.filter(production_priority__gte=min_priority)
    
    # Order by priority
    queryset = queryset.order_by('-production_priority', 'article')
    
    exporter = ProductsExporter()
    return exporter.export_products(queryset)
