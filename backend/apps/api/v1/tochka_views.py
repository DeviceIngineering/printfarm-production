from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from django.db.models import Q
from apps.products.models import Product
from apps.products.serializers import ProductListSerializer
import pandas as pd
import io
import re

def normalize_article(article):
    """
    Нормализация артикула для корректного сравнения
    - Удаляет лишние пробелы в начале и конце
    - Заменяет все виды тире на обычное тире
    - Удаляет невидимые символы
    - Приводит к стандартному виду
    """
    if not article:
        return ''
    
    # Конвертируем в строку и убираем пробелы
    article = str(article).strip()
    
    # Заменяем различные виды тире и дефисов на обычный дефис
    # Включает: en dash (–), em dash (—), minus (−), hyphen-minus (-)
    article = re.sub(r'[–—−‒]', '-', article)
    
    # Удаляем невидимые символы (кроме обычного пробела)
    article = re.sub(r'[\x00-\x1f\x7f-\x9f\xa0\u2000-\u200f\u2028-\u202f\u205f-\u206f]', '', article)
    
    # Удаляем лишние пробелы внутри строки
    article = re.sub(r'\s+', ' ', article).strip()
    
    return article

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
        raw_data = []
        processed_count = 0
        error_count = 0
        
        for index, row in df.iterrows():
            try:
                # Используем функцию нормализации для артикула
                raw_article = row[article_column] if pd.notna(row[article_column]) else ''
                article = normalize_article(raw_article)
                orders = row[orders_column] if pd.notna(row[orders_column]) else 0
                
                # Отладочная информация для конкретного артикула
                if '423' in str(article) and '51412' in str(article):
                    print(f"DEBUG: Найден артикул содержащий 423 и 51412 в Excel:")
                    print(f"  - Исходное значение: {repr(raw_article)}")
                    print(f"  - После нормализации: '{article}'")
                    print(f"  - Длина строки: {len(article)}")
                    print(f"  - Байты: {article.encode('utf-8')}")
                    print(f"  - Строка: {index + 1}")
                    print(f"  - Точное совпадение с '423-51412': {article == '423-51412'}")
                    print(f"  - ASCII коды: {[ord(c) for c in article]}")
                    print(f"  - Hex коды: {article.encode('utf-8').hex()}")
                    # Проверим различные варианты сравнения
                    test_article = '423-51412'
                    print(f"  - Сравнение с normalize_article('423-51412'): {article == normalize_article(test_article)}")
                    print(f"  - Содержит '423-51412': {'423-51412' in article}")
                    print(f"  - Содержит нормализованный: {normalize_article('423-51412') in article}")
                    
                    # Покажем каждый символ отдельно
                    print(f"  - Посимвольно: {[(i, c, ord(c), hex(ord(c))) for i, c in enumerate(article)]}")
                    
                    # Проверим разные варианты тире
                    variants = ['423-51412', '423–51412', '423—51412', '423−51412', '423‒51412']
                    for variant in variants:
                        print(f"  - Сравнение с '{variant}': {article == variant} (коды: {[ord(c) for c in variant]})")
                
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
                
                raw_data.append({
                    'article': article,
                    'orders': int(orders),
                    'row_number': index + 1
                })
                processed_count += 1
                
            except Exception as e:
                error_count += 1
                continue
        
        if not raw_data:
            return Response({
                'error': 'Не удалось извлечь данные из файла. Проверьте формат данных.',
                'processed_count': processed_count,
                'error_count': error_count
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Дедупликация по артикулу с суммированием заказов
        article_dict = {}
        duplicate_count = 0
        
        for item in raw_data:
            article = item['article']
            orders = item['orders']
            
            # Отладочная информация для конкретного артикула
            if '423' in str(article) and '51412' in str(article):
                print(f"DEBUG: Дедупликация артикула содержащего 423 и 51412:")
                print(f"  - Артикул: '{article}'")
                print(f"  - Заказы: {orders}")
                print(f"  - Уже есть в словаре: {article in article_dict}")
                print(f"  - ASCII коды артикула: {[ord(c) for c in article]}")
                print(f"  - Точное совпадение с '423-51412': {article == '423-51412'}")
                if article in article_dict:
                    print(f"  - Текущие заказы в словаре: {article_dict[article]['orders']}")
                    print(f"  - После сложения будет: {article_dict[article]['orders'] + orders}")
            
            if article in article_dict:
                # Суммируем заказы для дублирующихся артикулов
                article_dict[article]['orders'] += orders
                article_dict[article]['duplicate_rows'].append(item['row_number'])
                duplicate_count += 1
            else:
                # Первое вхождение артикула
                article_dict[article] = {
                    'article': article,
                    'orders': orders,
                    'row_number': item['row_number'],
                    'duplicate_rows': []
                }
        
        # Формируем финальный список без дубликатов
        extracted_data = []
        for article, data in article_dict.items():
            # Отладка для нашего артикула
            if '423' in str(article) and '51412' in str(article):
                print(f"DEBUG: Финальная обработка артикула {article}:")
                print(f"  - Итоговые заказы: {data['orders']}")
                print(f"  - Есть дубликаты: {len(data['duplicate_rows']) > 0}")
                print(f"  - Строки дубликатов: {data['duplicate_rows']}")
            
            extracted_data.append({
                'article': data['article'],
                'orders': data['orders'],
                'row_number': data['row_number'],
                'has_duplicates': len(data['duplicate_rows']) > 0,
                'duplicate_rows': data['duplicate_rows'] if data['duplicate_rows'] else None
            })
        
        # Сортируем по убыванию количества заказов
        extracted_data.sort(key=lambda x: x['orders'], reverse=True)
        
        return Response({
            'message': f'Файл успешно обработан. Уникальных артикулов: {len(extracted_data)}, дубликатов обработано: {duplicate_count}.',
            'data': extracted_data[:50],  # Показываем первые 50 записей
            'total_records': len(extracted_data),
            'total_raw_records': len(raw_data),
            'unique_articles': len(extracted_data),
            'duplicates_merged': duplicate_count,
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

@api_view(['POST'])
@permission_classes([AllowAny])
def merge_excel_with_products(request):
    """
    API для объединения данных из Excel с товарами по артикулу
    Excel содержит товары Точки, нужно найти товары МойСклад которых НЕТ в Точке
    """
    try:
        excel_data = request.data.get('excel_data', [])
        
        if not excel_data:
            return Response({
                'error': 'Нет данных Excel для объединения'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Нормализуем артикулы из Excel данных и создаем словари
        excel_articles = set()
        excel_dict = {}
        normalized_to_original = {}  # Словарь для обратного поиска
        
        for item in excel_data:
            if item.get('article'):
                original_article = item['article']
                normalized_article = normalize_article(original_article)
                
                if normalized_article:  # Если артикул не пустой после нормализации
                    excel_articles.add(normalized_article)
                    excel_dict[normalized_article] = item
                    normalized_to_original[normalized_article] = original_article
        
        if not excel_articles:
            return Response({
                'error': 'Не найдены артикулы в данных Excel'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Отладочная информация
        print(f"DEBUG: Получено {len(excel_articles)} нормализованных артикулов из Excel")
        print(f"DEBUG: Первые 10 артикулов Excel: {list(excel_articles)[:10]}")
        
        # Проверим есть ли наш тестовый артикул
        test_normalized = normalize_article('423-51412')
        print(f"DEBUG: Нормализованный '423-51412': '{test_normalized}'")
        print(f"DEBUG: Есть ли в Excel: {test_normalized in excel_articles}")
        print(f"DEBUG: Все артикулы с '423' в Excel: {[a for a in excel_articles if '423' in a]}")
        print(f"DEBUG: Словарь excel_dict содержит:")
        for key, value in list(excel_dict.items())[:5]:  # Показываем первые 5
            print(f"  '{key}': заказы={value.get('orders', 'N/A')}")
        if test_normalized in excel_dict:
            print(f"DEBUG: Данные для {test_normalized}: {excel_dict[test_normalized]}")
        
        # Загружаем ВСЕ товары из базы данных (МойСклад) которые требуют производства
        products_for_production = Product.objects.filter(
            production_needed__gt=0
        ).order_by('-production_priority', 'article')
        
        # Проверим есть ли в базе наш тестовый товар
        try:
            test_product = Product.objects.get(article='423-51412')
            print(f"DEBUG: Товар 423-51412 найден в базе:")
            print(f"  - ID: {test_product.id}")
            print(f"  - Артикул: '{test_product.article}'")
            print(f"  - Нормализованный: '{normalize_article(test_product.article)}'")
            print(f"  - К производству: {test_product.production_needed}")
            print(f"  - Есть в списке production: {test_product in products_for_production}")
            print(f"  - ASCII коды артикула из БД: {[ord(c) for c in test_product.article]}")
        except Product.DoesNotExist:
            print(f"DEBUG: Товар 423-51412 НЕ найден в базе данных")
            # Попробуем найти похожие
            similar = Product.objects.filter(article__contains='423').filter(article__contains='51412')
            print(f"DEBUG: Похожие товары с 423 и 51412: {[p.article for p in similar]}")
        
        # Объединяем данные
        merged_data = []
        in_tochka_count = 0
        not_in_tochka_count = 0
        
        for product in products_for_production:
            # Нормализуем артикул из базы данных для сравнения
            normalized_product_article = normalize_article(product.article)
            
            # Проверяем есть ли товар в Excel (Точке)
            excel_item = excel_dict.get(normalized_product_article)
            
            # Отладочная информация для конкретного артикула
            if '423-51412' in product.article:
                print(f"DEBUG: Анализ артикула содержащего 423-51412:")
                print(f"  - Оригинальный артикул из базы: '{product.article}'")
                print(f"  - Нормализованный артикул из базы: '{normalized_product_article}'")
                print(f"  - Есть в Excel словаре: {normalized_product_article in excel_dict}")
                print(f"  - Excel item: {excel_item}")
                print(f"  - Все Excel артикулы с '423': {[a for a in excel_articles if '423' in a]}")
                print(f"  - Прямое сравнение: {normalized_product_article == normalize_article('423-51412')}")
            
            if excel_item:
                # Товар ЕСТЬ в Точке - объединяем данные
                merged_item = {
                    # Данные из товаров МойСклад
                    'article': product.article,
                    'product_id': product.id,
                    'product_name': product.name,
                    'product_description': product.description,
                    'current_stock': float(product.current_stock),
                    'sales_last_2_months': float(product.sales_last_2_months),
                    'product_type': product.product_type,
                    'production_needed': float(product.production_needed),
                    'production_priority': product.production_priority,
                    'days_of_stock': float(product.days_of_stock) if product.days_of_stock else None,
                    
                    # Данные из Excel (Точка)
                    'orders_in_tochka': excel_item.get('orders', 0),
                    'excel_row_number': excel_item.get('row_number', 0),
                    'has_duplicates': excel_item.get('has_duplicates', False),
                    'duplicate_rows': excel_item.get('duplicate_rows'),
                    
                    # Статус
                    'is_in_tochka': True,
                    'needs_registration': False,
                }
                in_tochka_count += 1
            else:
                # Товара НЕТ в Точке - помечаем специально
                merged_item = {
                    # Данные из товаров МойСклад
                    'article': product.article,
                    'product_id': product.id,
                    'product_name': product.name,
                    'product_description': product.description,
                    'current_stock': float(product.current_stock),
                    'sales_last_2_months': float(product.sales_last_2_months),
                    'product_type': product.product_type,
                    'production_needed': float(product.production_needed),
                    'production_priority': product.production_priority,
                    'days_of_stock': float(product.days_of_stock) if product.days_of_stock else None,
                    
                    # Пустые данные Точки
                    'orders_in_tochka': 0,
                    'excel_row_number': None,
                    'has_duplicates': False,
                    'duplicate_rows': None,
                    
                    # Статус
                    'is_in_tochka': False,
                    'needs_registration': True,  # Нужно завести в Точке!
                }
                not_in_tochka_count += 1
            
            merged_data.append(merged_item)
        
        # Сортируем: сначала товары которых нет в Точке, потом по приоритету производства
        merged_data.sort(key=lambda x: (not x['needs_registration'], -x['production_priority']))
        
        return Response({
            'message': f'Анализ завершен. Товаров в Точке: {in_tochka_count}, отсутствует в Точке: {not_in_tochka_count}',
            'data': merged_data,
            'total_production_needed': len(merged_data),
            'products_in_tochka': in_tochka_count,
            'products_not_in_tochka': not_in_tochka_count,
            'coverage_rate': round((in_tochka_count / len(merged_data)) * 100, 1) if merged_data else 0,
        })
        
    except Exception as e:
        return Response({
            'error': f'Ошибка при объединении данных: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([AllowAny])
def get_filtered_production_list(request):
    """
    API для получения отфильтрованного списка на производство
    Возвращает только товары которые ЕСТЬ в Точке (исключает товары отсутствующие в Точке)
    """
    try:
        excel_data = request.data.get('excel_data', [])
        
        if not excel_data:
            return Response({
                'error': 'Нет данных Excel для фильтрации'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Нормализуем артикулы из Excel данных
        excel_articles = set()
        excel_dict = {}
        
        for item in excel_data:
            if item.get('article'):
                normalized_article = normalize_article(item['article'])
                if normalized_article:
                    excel_articles.add(normalized_article)
                    excel_dict[normalized_article] = item
        
        if not excel_articles:
            return Response({
                'error': 'Не найдены артикулы в данных Excel'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Загружаем ВСЕ товары на производство и фильтруем те, которые ЕСТЬ в Точке
        all_products_for_production = Product.objects.filter(
            production_needed__gt=0
        ).order_by('-production_priority', 'article')
        
        # Фильтруем товары, которые есть в Excel (Точке)
        products_in_tochka = []
        for product in all_products_for_production:
            normalized_product_article = normalize_article(product.article)
            if normalized_product_article in excel_articles:
                products_in_tochka.append(product)
        
        # Формируем отфильтрованный список на производство
        production_list = []
        total_quantity = 0
        
        for product in products_in_tochka:
            normalized_product_article = normalize_article(product.article)
            excel_item = excel_dict.get(normalized_product_article, {})
            
            item = {
                'article': product.article,
                'product_name': product.name,
                'production_needed': float(product.production_needed),
                'production_priority': product.production_priority,
                'current_stock': float(product.current_stock),
                'product_type': product.product_type,
                'sales_last_2_months': float(product.sales_last_2_months),
                'orders_in_tochka': excel_item.get('orders', 0),
                'has_duplicates': excel_item.get('has_duplicates', False),
            }
            
            production_list.append(item)
            total_quantity += float(product.production_needed)
        
        return Response({
            'message': f'Отфильтрованный список готов: {len(production_list)} товаров к производству',
            'data': production_list,
            'total_items': len(production_list),
            'total_quantity': round(total_quantity, 2),
            'filtered_by_tochka': True,
        })
        
    except Exception as e:
        return Response({
            'error': f'Ошибка при создании отфильтрованного списка: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([AllowAny])
def debug_article_matching(request):
    """
    DEBUG API для проверки сопоставления артикулов
    """
    try:
        excel_data = request.data.get('excel_data', [])
        test_article = request.data.get('test_article', '423-51412')
        
        # Анализируем Excel данные с нормализацией
        excel_articles = set()
        excel_dict = {}
        
        for item in excel_data:
            if item.get('article'):
                original_article = item['article']
                normalized_article = normalize_article(original_article)
                if normalized_article:
                    excel_articles.add(normalized_article)
                    excel_dict[normalized_article] = item
        
        # Нормализуем тестовый артикул
        normalized_test_article = normalize_article(test_article)
        
        # Ищем товар в базе данных
        try:
            product = Product.objects.get(article=test_article)
            product_found = True
            product_info = {
                'id': product.id,
                'article': product.article,
                'normalized_article': normalize_article(product.article),
                'name': product.name,
                'production_needed': float(product.production_needed)
            }
        except Product.DoesNotExist:
            product_found = False
            product_info = None
        
        # Проверяем в Excel (используем нормализованные артикулы)
        excel_found = normalized_test_article in excel_articles
        excel_item = excel_dict.get(normalized_test_article)
        
        return Response({
            'test_article': test_article,
            'normalized_test_article': normalized_test_article,
            'product_found_in_db': product_found,
            'product_info': product_info,
            'excel_found': excel_found,
            'excel_item': excel_item,
            'total_excel_articles': len(excel_articles),
            'excel_articles_sample': list(excel_articles)[:20],
            'matching_articles': [a for a in excel_articles if normalized_test_article in a],
            'debug_info': {
                'normalized_exact_match': normalized_test_article in excel_dict,
                'normalization_test': {
                    'original_423-51412': '423-51412',
                    'normalized_423-51412': normalize_article('423-51412'),
                    'comparison_result': normalized_test_article == normalize_article('423-51412')
                },
                'excel_articles_with_423': [a for a in excel_articles if '423' in a],
                'all_dashes_in_test': [ord(c) for c in normalized_test_article if c in '–—−‒-']
            }
        })
        
    except Exception as e:
        return Response({
            'error': f'Ошибка отладки: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([AllowAny])
def trace_article_processing(request):
    """
    DEBUG API для пошагового отслеживания обработки артикула
    """
    try:
        excel_data = request.data.get('excel_data', [])
        test_article = request.data.get('test_article', '423-51412')
        
        result = {
            'test_article': test_article,
            'steps': []
        }
        
        # Шаг 1: Поиск в исходных Excel данных
        found_in_raw = []
        for i, item in enumerate(excel_data):
            if test_article in str(item.get('article', '')):
                found_in_raw.append({
                    'index': i,
                    'original_article': item.get('article'),
                    'orders': item.get('orders'),
                    'exact_match': item.get('article') == test_article
                })
        
        result['steps'].append({
            'step': 1,
            'name': 'Поиск в исходных Excel данных',
            'found_count': len(found_in_raw),
            'details': found_in_raw
        })
        
        # Шаг 2: После нормализации
        normalized_articles = {}
        for item in excel_data:
            if item.get('article'):
                original = item['article']
                normalized = normalize_article(original)
                if test_article in original or normalize_article(test_article) == normalized:
                    normalized_articles[original] = {
                        'normalized': normalized,
                        'orders': item.get('orders'),
                        'match_original': test_article in original,
                        'match_normalized': normalize_article(test_article) == normalized
                    }
        
        result['steps'].append({
            'step': 2,
            'name': 'После нормализации артикулов',
            'test_normalized': normalize_article(test_article),
            'found_articles': normalized_articles
        })
        
        # Шаг 3: Проверка в базе данных
        try:
            product = Product.objects.get(article=test_article)
            db_info = {
                'found': True,
                'id': product.id,
                'article': product.article,
                'normalized_article': normalize_article(product.article),
                'production_needed': float(product.production_needed),
                'is_for_production': product.production_needed > 0
            }
        except Product.DoesNotExist:
            # Попробуем найти похожие
            similar = Product.objects.filter(article__icontains='423-51412')
            db_info = {
                'found': False,
                'similar_products': [{'article': p.article, 'normalized': normalize_article(p.article)} for p in similar]
            }
        
        result['steps'].append({
            'step': 3,
            'name': 'Проверка в базе данных',
            'details': db_info
        })
        
        return Response(result)
        
    except Exception as e:
        return Response({
            'error': f'Ошибка трассировки: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)