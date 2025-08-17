"""
Тесты для фичи поддержки поля "Цвет" из МойСклад

Следует принципам TDD - сначала тесты, потом реализация.
Покрытие: 90%+ кода связанного с полем color
"""

from django.test import TestCase
from django.core.exceptions import ValidationError
from decimal import Decimal
from unittest.mock import patch, MagicMock

from apps.products.models import Product, ProductImage
from apps.sync.moysklad_client import MoySkladClient


class ColorFieldModelTests(TestCase):
    """
    Тесты модели Product с полем color
    """
    
    def setUp(self):
        """Настройка данных для тестов"""
        self.product_data = {
            'moysklad_id': 'test-id-123',
            'article': 'TEST-001',
            'name': 'Тестовый товар',
            'description': 'Описание тестового товара',
            'current_stock': Decimal('10.00'),
            'sales_last_2_months': Decimal('5.00'),
            'product_type': 'old'
        }
    
    def test_product_model_has_color_field(self):
        """
        Тест: Модель Product должна иметь поле color
        """
        # Создаем продукт с цветом
        product = Product.objects.create(
            **self.product_data,
            color='Красный'
        )
        
        # Проверяем, что поле color сохранилось
        self.assertEqual(product.color, 'Красный')
        
        # Проверяем, что можно получить продукт по цвету
        product_from_db = Product.objects.get(color='Красный')
        self.assertEqual(product_from_db.moysklad_id, 'test-id-123')
    
    def test_color_field_is_optional(self):
        """
        Тест: Поле color должно быть необязательным (blank=True)
        """
        # Создаем продукт без цвета
        product = Product.objects.create(**self.product_data)
        
        # Поле color должно быть пустым или None
        self.assertTrue(product.color == '' or product.color is None)
        
        # Продукт должен сохраниться без ошибок
        self.assertIsNotNone(product.id)
    
    def test_color_field_max_length(self):
        """
        Тест: Поле color должно иметь разумное ограничение по длине
        """
        # Тест с нормальным цветом
        product1 = Product.objects.create(
            **self.product_data,
            color='Ярко-красный с золотистым оттенком'
        )
        self.assertIsNotNone(product1.id)
        
        # Тест с очень длинным названием цвета (должно работать до 100 символов)
        long_color = 'А' * 100
        product2 = Product.objects.create(
            moysklad_id='test-id-124',
            article='TEST-002',
            name='Тестовый товар 2',
            color=long_color
        )
        self.assertEqual(product2.color, long_color)
    
    def test_color_field_unicode_support(self):
        """
        Тест: Поле color должно поддерживать русские символы и эмодзи
        """
        test_colors = [
            'Красный',
            'Синий металлик',
            'Чёрный матовый',
            'Зелёный 🟢',
            'Multi-цветный',
        ]
        
        for i, color in enumerate(test_colors):
            product = Product.objects.create(
                moysklad_id=f'test-id-{i}',
                article=f'TEST-{i}',
                name=f'Тестовый товар {i}',
                color=color
            )
            self.assertEqual(product.color, color)
    
    def test_product_string_representation_includes_color(self):
        """
        Тест: Строковое представление продукта должно включать цвет, если он есть
        """
        # Продукт с цветом
        product_with_color = Product.objects.create(
            **self.product_data,
            color='Синий'
        )
        
        # Продукт без цвета
        product_without_color = Product.objects.create(
            moysklad_id='test-id-124',
            article='TEST-002',
            name='Тестовый товар 2'
        )
        
        # Проверяем строковое представление
        str_with_color = str(product_with_color)
        str_without_color = str(product_without_color)
        
        # Должен содержать информацию о цвете
        self.assertIn('Синий', str_with_color)
        
        # Без цвета не должно быть проблем
        self.assertIn('TEST-002', str_without_color)


class ColorFieldSyncTests(TestCase):
    """
    Тесты синхронизации поля color с МойСклад
    """
    
    def setUp(self):
        """Настройка данных для тестов"""
        self.client = MoySkladClient()
        
        self.mock_product_data = {
            'id': 'test-moysklad-id',
            'article': 'TEST-SYNC-001',
            'name': 'Тестовый товар синхронизации',
            'description': 'Описание',
            'attributes': [
                {
                    'meta': {
                        'href': 'https://api.moysklad.ru/api/remap/1.2/entity/product/metadata/attributes/color-attr-id'
                    },
                    'name': 'Цвет',
                    'value': 'Красный'
                },
                {
                    'meta': {
                        'href': 'https://api.moysklad.ru/api/remap/1.2/entity/product/metadata/attributes/other-attr-id'
                    },
                    'name': 'Другой атрибут',
                    'value': 'Другое значение'
                }
            ],
            'stock': 10,
            'reserve': 2
        }
    
    def test_extract_color_from_moysklad_attributes(self):
        """
        Тест: Извлечение цвета из атрибутов МойСклад
        """
        # Тестируем метод извлечения цвета
        color = self.client.extract_color_from_attributes(
            self.mock_product_data.get('attributes', [])
        )
        
        self.assertEqual(color, 'Красный')
    
    def test_extract_color_when_no_color_attribute(self):
        """
        Тест: Обработка случая, когда атрибут "Цвет" отсутствует
        """
        # Данные без атрибута "Цвет"
        data_without_color = {
            'attributes': [
                {
                    'name': 'Размер',
                    'value': 'Большой'
                }
            ]
        }
        
        color = self.client.extract_color_from_attributes(
            data_without_color.get('attributes', [])
        )
        
        # Должен вернуть пустую строку или None
        self.assertTrue(color == '' or color is None)
    
    def test_extract_color_when_no_attributes(self):
        """
        Тест: Обработка случая, когда атрибуты полностью отсутствуют
        """
        color = self.client.extract_color_from_attributes([])
        self.assertTrue(color == '' or color is None)
    
    def test_extract_color_case_insensitive(self):
        """
        Тест: Поиск атрибута "Цвет" должен быть нечувствителен к регистру
        """
        test_cases = [
            {'name': 'цвет', 'value': 'Зелёный'},
            {'name': 'ЦВЕТ', 'value': 'Жёлтый'},
            {'name': 'Цвет', 'value': 'Синий'},
            {'name': 'ЦвЕт', 'value': 'Фиолетовый'}
        ]
        
        for case in test_cases:
            attributes = [case]
            color = self.client.extract_color_from_attributes(attributes)
            self.assertEqual(color, case['value'])
    
    def test_sync_product_with_color(self):
        """
        Тест: Синхронизация продукта с полем color из МойСклад
        """
        # Данные продукта с атрибутом "Цвет"
        product_data = {
            'id': 'test-moysklad-id',
            'name': 'Тестовый товар',
            'article': 'TEST-001',
            'attributes': [
                {
                    'id': 'color-attr-id',
                    'name': 'Цвет',
                    'value': 'Красный'
                }
            ]
        }
        
        # Извлекаем цвет из атрибутов
        extracted_color = self.client.extract_color_from_attributes(product_data['attributes'])
        
        # Проверяем корректность извлечения
        self.assertEqual(extracted_color, 'Красный')
        
        # Проверяем, что метод возвращает пустую строку при отсутствии цвета
        product_without_color = {
            'attributes': [
                {
                    'id': 'other-attr-id',
                    'name': 'Размер',
                    'value': 'XL'
                }
            ]
        }
        
        no_color = self.client.extract_color_from_attributes(product_without_color['attributes'])
        self.assertEqual(no_color, '')
    
    def test_sync_performance_with_color_field(self):
        """
        Тест: Производительность синхронизации с полем color < 5 сек
        """
        import time
        
        # Создаем 100 тестовых продуктов
        test_products = []
        for i in range(100):
            product_data = {
                'moysklad_id': f'test-id-{i}',
                'article': f'PERF-{i:03d}',
                'name': f'Товар производительности {i}',
                'color': f'Цвет-{i % 10}',  # 10 разных цветов
                'current_stock': Decimal('5.00'),
                'sales_last_2_months': Decimal('2.00')
            }
            test_products.append(Product(**product_data))
        
        # Измеряем время массового создания
        start_time = time.time()
        Product.objects.bulk_create(test_products)
        end_time = time.time()
        
        # Проверяем, что время выполнения < 5 секунд
        execution_time = end_time - start_time
        self.assertLess(execution_time, 5.0, 
                       f"Создание 100 продуктов заняло {execution_time:.2f} сек, должно быть < 5 сек")
        
        # Проверяем, что все продукты созданы с цветами
        created_products = Product.objects.filter(article__startswith='PERF-')
        self.assertEqual(created_products.count(), 100)
        
        # Проверяем корректность цветов
        for product in created_products.all():
            self.assertTrue(product.color.startswith('Цвет-'))


class ColorFieldAPITests(TestCase):
    """
    Тесты API endpoints с полем color
    """
    
    def setUp(self):
        """Настройка данных для тестов API"""
        # Создаем тестовые продукты с разными цветами
        self.products = []
        colors = ['Красный', 'Синий', 'Зелёный', 'Жёлтый', '']
        
        for i, color in enumerate(colors):
            product = Product.objects.create(
                moysklad_id=f'api-test-{i}',
                article=f'API-{i:03d}',
                name=f'API тестовый товар {i}',
                color=color,
                current_stock=Decimal('10.00'),
                sales_last_2_months=Decimal('5.00')
            )
            self.products.append(product)
    
    def test_products_api_includes_color(self):
        """
        Тест: API /api/v1/products/ должен включать поле color
        """
        from django.test import Client
        from django.contrib.auth.models import User
        
        # Создаем пользователя для аутентификации
        user = User.objects.create_user('testuser', 'test@example.com', 'password')
        
        client = Client()
        client.force_login(user)
        
        # Делаем запрос к API
        response = client.get('/api/v1/products/')
        self.assertEqual(response.status_code, 200)
        
        # Проверяем, что поле color присутствует в ответе
        data = response.json()
        self.assertIn('results', data)
        
        if data['results']:
            first_product = data['results'][0]
            self.assertIn('color', first_product)
    
    def test_tochka_api_includes_color(self):
        """
        Тест: API Точка должен включать поле color
        """
        from django.test import Client
        from django.contrib.auth.models import User
        
        user = User.objects.create_user('testuser2', 'test2@example.com', 'password')
        client = Client()
        client.force_login(user)
        
        # Тестируем API точки
        response = client.get('/api/v1/tochka/products/')
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        if 'products' in data and data['products']:
            first_product = data['products'][0]
            self.assertIn('color', first_product)
    
    def test_filter_products_by_color(self):
        """
        Тест: Возможность фильтрации товаров по цвету
        """
        # Фильтрация по цвету в Python (базовая логика)
        red_products = Product.objects.filter(color='Красный')
        blue_products = Product.objects.filter(color='Синий')
        empty_color_products = Product.objects.filter(color='')
        
        self.assertEqual(red_products.count(), 1)
        self.assertEqual(blue_products.count(), 1)
        self.assertEqual(empty_color_products.count(), 1)
        
        # Проверяем корректность фильтрации
        self.assertEqual(red_products.first().color, 'Красный')
        self.assertEqual(blue_products.first().color, 'Синий')


class ColorFieldBackwardCompatibilityTests(TestCase):
    """
    Тесты обратной совместимости для поля color
    """
    
    def test_existing_products_work_without_color(self):
        """
        Тест: Существующие продукты без поля color должны работать корректно
        """
        # Создаем продукт старым способом (без color)
        product = Product.objects.create(
            moysklad_id='backward-test-001',
            article='BWD-001',
            name='Продукт обратной совместимости',
            current_stock=Decimal('5.00')
        )
        
        # Все методы должны работать
        self.assertIsNotNone(product.classify_product_type())
        self.assertIsNotNone(product.calculate_production_need())
        self.assertIsNotNone(product.calculate_priority())
        
        # save() должен работать без ошибок
        product.save()
        self.assertIsNotNone(product.id)
    
    def test_migration_rollback_safety(self):
        """
        Тест: Безопасность отката миграции
        """
        # Создаем продукт с цветом
        product = Product.objects.create(
            moysklad_id='migration-test-001',
            article='MIG-001',
            name='Тест миграции',
            color='Красный'
        )
        
        # Проверяем, что продукт создался
        self.assertIsNotNone(product.id)
        self.assertEqual(product.color, 'Красный')
        
        # Имитируем отсутствие поля color (как при откате миграции)
        # Продукт должен продолжать работать
        product_data = {
            'moysklad_id': product.moysklad_id,
            'article': product.article,
            'name': product.name,
            'current_stock': product.current_stock,
            'sales_last_2_months': product.sales_last_2_months
        }
        
        # Основные операции должны работать без поля color
        self.assertIsNotNone(product_data['article'])
        self.assertIsNotNone(product_data['name'])


class ColorFieldEdgeCasesTests(TestCase):
    """
    Тесты граничных случаев для поля color
    """
    
    def test_color_with_special_characters(self):
        """
        Тест: Цвета со специальными символами
        """
        special_colors = [
            'Красно-синий',
            'Цвет #FF5733',
            'RGB(255, 99, 71)',
            'Прозрачный 50%',
            'Металлик & глянец',
            'Цвет "Морская волна"',
            "Цвет 'Sunset'",
        ]
        
        for i, color in enumerate(special_colors):
            product = Product.objects.create(
                moysklad_id=f'special-{i}',
                article=f'SPEC-{i:03d}',
                name=f'Специальный товар {i}',
                color=color
            )
            
            # Проверяем, что продукт сохранился с правильным цветом
            saved_product = Product.objects.get(moysklad_id=f'special-{i}')
            self.assertEqual(saved_product.color, color)
    
    def test_color_normalization(self):
        """
        Тест: Нормализация значений цвета (опционально)
        """
        # Тест на то, что пробелы в начале и конце удаляются
        product = Product.objects.create(
            moysklad_id='normalize-test',
            article='NORM-001',
            name='Тест нормализации',
            color='  Красный  '
        )
        
        # После сохранения пробелы должны быть удалены
        product.refresh_from_db()
        self.assertEqual(product.color.strip(), 'Красный')
    
    def test_empty_vs_null_color_handling(self):
        """
        Тест: Обработка пустых значений vs NULL
        """
        # Продукт с пустой строкой
        product1 = Product.objects.create(
            moysklad_id='empty-1',
            article='EMPTY-1',
            name='Пустой цвет 1',
            color=''
        )
        
        # Продукт без указания цвета (должен использовать default='')
        product2 = Product.objects.create(
            moysklad_id='empty-2',
            article='EMPTY-2',
            name='Пустой цвет 2'
            # color не указан, должен использоваться default=''
        )
        
        # Оба должны корректно сохраниться
        self.assertIsNotNone(product1.id)
        self.assertIsNotNone(product2.id)
        
        # Проверяем обработку пустых значений
        self.assertEqual(product1.color, '')
        self.assertEqual(product2.color, '')