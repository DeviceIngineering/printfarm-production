from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from django.db.models import Q
from apps.products.models import Product
from apps.products.serializers import ProductListSerializer

@api_view(['GET'])
@permission_classes([AllowAny])
def get_products_for_tochka(request):
    """
    API для получения списка всех товаров для вкладки Точка
    """
    try:
        # Получаем все товары с базовой информацией
        products = Product.objects.all().order_by('-updated_at')
        
        # Применяем пагинацию если нужно
        limit = request.GET.get('limit')
        if limit:
            try:
                limit = int(limit)
                products = products[:limit]
            except ValueError:
                pass
        
        # Сериализация данных
        serializer = ProductListSerializer(products, many=True, context={'request': request})
        
        return Response({
            'results': serializer.data,
            'count': len(serializer.data),
            'message': 'Товары успешно загружены'
        })
        
    except Exception as e:
        return Response({
            'error': f'Ошибка при загрузке товаров: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([AllowAny])
def get_production_list_for_tochka(request):
    """
    API для получения списка товаров на производство для вкладки Точка
    """
    try:
        # Получаем только товары, которые требуют производства
        products = Product.objects.filter(
            production_needed__gt=0
        ).order_by('-production_priority', 'article')
        
        # Применяем пагинацию если нужно
        limit = request.GET.get('limit')
        if limit:
            try:
                limit = int(limit)
                products = products[:limit]
            except ValueError:
                pass
        
        # Сериализация данных
        serializer = ProductListSerializer(products, many=True, context={'request': request})
        
        return Response({
            'results': serializer.data,
            'count': len(serializer.data),
            'message': 'Список на производство успешно загружен'
        })
        
    except Exception as e:
        return Response({
            'error': f'Ошибка при загрузке списка на производство: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([AllowAny])
def get_products_stats_for_tochka(request):
    """
    API для получения статистики товаров для вкладки Точка
    """
    try:
        total_products = Product.objects.count()
        production_needed = Product.objects.filter(production_needed__gt=0).count()
        critical_products = Product.objects.filter(product_type='critical').count()
        new_products = Product.objects.filter(product_type='new').count()
        old_products = Product.objects.filter(product_type='old').count()
        
        return Response({
            'total_products': total_products,
            'production_needed': production_needed,
            'critical_products': critical_products,
            'new_products': new_products,
            'old_products': old_products,
            'message': 'Статистика успешно загружена'
        })
        
    except Exception as e:
        return Response({
            'error': f'Ошибка при загрузке статистики: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)