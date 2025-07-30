from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from django.db.models import Q
from apps.products.models import Product
from apps.products.serializers import ProductListSerializer
import pandas as pd
import io

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

@api_view(['POST'])
@permission_classes([AllowAny])
def upload_excel_file_for_tochka(request):
    """
    API для загрузки Excel файла с данными для вкладки Точка
    Ищет колонки "Артикул товара" и "Заказов, шт."
    """
    try:
        if 'file' not in request.FILES:
            return Response({
                'error': 'Файл не найден. Пожалуйста, выберите Excel файл.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        excel_file = request.FILES['file']
        
        # Проверяем расширение файла
        if not excel_file.name.endswith(('.xlsx', '.xls')):
            return Response({
                'error': 'Неверный формат файла. Поддерживаются только .xlsx и .xls файлы.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Читаем Excel файл
        try:
            if excel_file.name.endswith('.xlsx'):
                df = pd.read_excel(io.BytesIO(excel_file.read()), engine='openpyxl')
            else:
                df = pd.read_excel(io.BytesIO(excel_file.read()), engine='xlrd')
        except Exception as e:
            return Response({
                'error': f'Ошибка при чтении Excel файла: {str(e)}'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Ищем нужные колонки
        article_column = None
        orders_column = None
        
        # Возможные варианты названий колонок
        article_variants = ['Артикул товара', 'артикул товара', 'Артикул', 'артикул', 'Article', 'article']
        orders_variants = ['Заказов, шт.', 'заказов, шт.', 'Заказов шт', 'заказов шт', 'Заказов', 'заказов', 'Orders', 'orders']
        
        # Поиск колонки с артикулами
        for col in df.columns:
            if str(col).strip() in article_variants:
                article_column = col
                break
        
        # Поиск колонки с заказами
        for col in df.columns:
            if str(col).strip() in orders_variants:
                orders_column = col
                break
        
        if article_column is None:
            return Response({
                'error': 'Колонка "Артикул товара" не найдена в файле.',
                'available_columns': list(df.columns)
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if orders_column is None:
            return Response({
                'error': 'Колонка "Заказов, шт." не найдена в файле.',
                'available_columns': list(df.columns)
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Извлекаем данные из нужных колонок
        extracted_data = []
        processed_count = 0
        error_count = 0
        
        for index, row in df.iterrows():
            try:
                article = str(row[article_column]).strip() if pd.notna(row[article_column]) else ''
                orders = row[orders_column] if pd.notna(row[orders_column]) else 0
                
                # Пропускаем пустые артикулы
                if not article or article.lower() in ['nan', 'none', '']:
                    continue
                
                # Пытаемся преобразовать количество заказов в число
                try:
                    orders = float(orders)
                    if orders < 0:
                        orders = 0
                except (ValueError, TypeError):
                    orders = 0
                
                extracted_data.append({
                    'article': article,
                    'orders': int(orders),
                    'row_number': index + 1
                })
                processed_count += 1
                
            except Exception as e:
                error_count += 1
                continue
        
        if not extracted_data:
            return Response({
                'error': 'Не удалось извлечь данные из файла. Проверьте формат данных.',
                'processed_count': processed_count,
                'error_count': error_count
            }, status=status.HTTP_400_BAD_REQUEST)
        
        return Response({
            'message': f'Файл успешно обработан. Загружено {len(extracted_data)} записей.',
            'data': extracted_data[:50],  # Показываем первые 50 записей
            'total_records': len(extracted_data),
            'processed_count': processed_count,
            'error_count': error_count,
            'columns_found': {
                'article_column': article_column,
                'orders_column': orders_column
            }
        })
        
    except Exception as e:
        return Response({
            'error': f'Внутренняя ошибка сервера: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)