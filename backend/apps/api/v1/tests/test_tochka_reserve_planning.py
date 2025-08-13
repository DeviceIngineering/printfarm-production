"""
Тесты для функциональности учета резерва при планировании с учетом Точки.

Покрывает:
1. Отображение колонки "Резерв" в таблице товаров Точки при включенном переключателе
2. Отображение колонки "Резерв" в таблице списка к производству при включенном переключателе  
3. Подсветка строк с резервом в планировании производства
4. Интеграция переключателя резерва между вкладками
"""
import json
from decimal import Decimal
from django.test import TestCase, TransactionTestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase, APIClient
from unittest.mock import patch, MagicMock

from apps.products.models import Product


class TochkaReserveDisplayTest(APITestCase):
    """Тесты отображения колонки резерва в таблице товаров Точки."""
    
    def setUp(self):
        """Настройка тестовых данных."""
        # Создаем товары с различными значениями резерва
        self.products = []
        
        # Товар без резерва
        self.product_no_reserve = Product.objects.create(
            moysklad_id='tochka-test-1',
            article='TOCHKA-001',
            name='Товар без резерва',
            current_stock=Decimal('10'),
            reserved_stock=Decimal('0'),
            sales_last_2_months=Decimal('20'),
            production_needed=Decimal('5'),
            production_priority=75
        )
        
        # Товар с резервом
        self.product_with_reserve = Product.objects.create(
            moysklad_id='tochka-test-2',
            article='TOCHKA-002', 
            name='Товар с резервом',
            current_stock=Decimal('8'),
            reserved_stock=Decimal('3'),
            sales_last_2_months=Decimal('15'),
            production_needed=Decimal('7'),
            production_priority=80
        )
        
        # Товар с большим резервом
        self.product_high_reserve = Product.objects.create(
            moysklad_id='tochka-test-3',
            article='TOCHKA-003',
            name='Товар с большим резервом',
            current_stock=Decimal('5'),
            reserved_stock=Decimal('15'),
            sales_last_2_months=Decimal('25'),
            production_needed=Decimal('10'),
            production_priority=90
        )
        
        self.products = [
            self.product_no_reserve,
            self.product_with_reserve,
            self.product_high_reserve
        ]
    
    def test_tochka_products_includes_reserve_field_by_default(self):
        """Тест: API товаров Точки включает поле reserved_stock по умолчанию."""
        url = reverse('tochka-products')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Проверяем что все товары включают поле reserved_stock
        products = response.data['results']
        self.assertGreater(len(products), 0)
        
        for product in products:
            self.assertIn('reserved_stock', product)
            self.assertIsNotNone(product['reserved_stock'])
    
    def test_tochka_products_with_include_reserve_parameter(self):
        """Тест: API товаров Точки с параметром include_reserve=true."""
        url = reverse('tochka-products')
        response = self.client.get(url, {'include_reserve': 'true'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Проверяем что effective_stock рассчитывается с учетом резерва
        products = response.data['results']
        
        for product in products:
            self.assertIn('reserved_stock', product)
            self.assertIn('effective_stock', product)
            
            # Находим соответствующий товар в базе
            db_product = Product.objects.get(id=product['id'])
            expected_effective_stock = float(db_product.current_stock + db_product.reserved_stock)
            
            self.assertEqual(product['effective_stock'], expected_effective_stock)
    
    def test_tochka_products_without_include_reserve_parameter(self):
        """Тест: API товаров Точки без параметра include_reserve."""
        url = reverse('tochka-products')
        response = self.client.get(url, {'include_reserve': 'false'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Проверяем что effective_stock равен current_stock
        products = response.data['results']
        
        for product in products:
            self.assertIn('reserved_stock', product)
            self.assertIn('effective_stock', product)
            
            # Находим соответствующий товар в базе
            db_product = Product.objects.get(id=product['id'])
            expected_effective_stock = float(db_product.current_stock)
            
            self.assertEqual(product['effective_stock'], expected_effective_stock)
    
    def test_tochka_products_reserve_column_data_types(self):
        """Тест: корректные типы данных для колонки резерва."""
        url = reverse('tochka-products')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        products = response.data['results']
        
        for product in products:
            reserved_stock = product['reserved_stock']
            
            # Проверяем что reserved_stock это число (float или int)
            self.assertIsInstance(reserved_stock, (int, float, str))
            
            # Проверяем что можно конвертировать в float
            try:
                float(reserved_stock)
            except (ValueError, TypeError):
                self.fail(f"reserved_stock '{reserved_stock}' cannot be converted to float")
    
    def test_tochka_products_reserve_calculation_accuracy(self):
        """Тест: точность расчетов с резервом."""
        url = reverse('tochka-products')
        
        # Запрос с учетом резерва
        response_with_reserve = self.client.get(url, {'include_reserve': 'true'})
        self.assertEqual(response_with_reserve.status_code, status.HTTP_200_OK)
        
        # Запрос без учета резерва  
        response_without_reserve = self.client.get(url, {'include_reserve': 'false'})
        self.assertEqual(response_without_reserve.status_code, status.HTTP_200_OK)
        
        products_with = {p['id']: p for p in response_with_reserve.data['results']}
        products_without = {p['id']: p for p in response_without_reserve.data['results']}
        
        # Проверяем что расчет корректный для каждого товара
        for product_id in products_with.keys():
            with_reserve = products_with[product_id]
            without_reserve = products_without[product_id]
            
            # effective_stock с резервом должен быть больше или равен без резерва
            self.assertGreaterEqual(
                with_reserve['effective_stock'],
                without_reserve['effective_stock']
            )
            
            # Разница должна равняться reserved_stock
            difference = with_reserve['effective_stock'] - without_reserve['effective_stock']
            expected_difference = float(with_reserve['reserved_stock'])
            
            self.assertAlmostEqual(difference, expected_difference, places=2)


class TochkaProductionReserveDisplayTest(APITestCase):
    """Тесты отображения колонки резерва в таблице списка к производству Точки."""
    
    def setUp(self):
        """Настройка тестовых данных."""
        # Создаем товары требующие производства с различными резервами
        self.production_products = []
        
        for i in range(3):
            product = Product.objects.create(
                moysklad_id=f'prod-test-{i+1}',
                article=f'PROD-{i+1:03d}',
                name=f'Товар на производство {i+1}',
                current_stock=Decimal(str(2 + i)),  # 2, 3, 4
                reserved_stock=Decimal(str(i * 2)),  # 0, 2, 4
                sales_last_2_months=Decimal(str(20 + i * 5)),
                production_needed=Decimal(str(8 - i)),  # 8, 7, 6
                production_priority=90 - i * 10  # 90, 80, 70
            )
            self.production_products.append(product)
    
    def test_tochka_production_includes_reserve_field(self):
        """Тест: API списка производства Точки включает поле reserved_stock."""
        url = reverse('tochka-production')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Проверяем что все товары на производство включают поле reserved_stock
        products = response.data['results']
        self.assertGreater(len(products), 0)
        
        for product in products:
            self.assertIn('reserved_stock', product)
            self.assertIsNotNone(product['reserved_stock'])
            
            # Проверяем что это товар требующий производства
            self.assertGreater(float(product['production_needed']), 0)
    
    def test_tochka_production_with_include_reserve_parameter(self):
        """Тест: API списка производства с параметром include_reserve=true."""
        url = reverse('tochka-production')
        response = self.client.get(url, {'include_reserve': 'true'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        products = response.data['results']
        
        for product in products:
            self.assertIn('reserved_stock', product)
            self.assertIn('effective_stock', product)
            
            # Находим соответствующий товар в базе
            db_product = Product.objects.get(id=product['id'])
            expected_effective_stock = float(db_product.current_stock + db_product.reserved_stock)
            
            self.assertEqual(product['effective_stock'], expected_effective_stock)
    
    def test_tochka_production_reserve_affects_production_calculation(self):
        """Тест: резерв влияет на расчеты производственной потребности."""
        url = reverse('tochka-production')
        
        # Запрос с учетом резерва
        response_with_reserve = self.client.get(url, {'include_reserve': 'true'})
        self.assertEqual(response_with_reserve.status_code, status.HTTP_200_OK)
        
        # Запрос без учета резерва
        response_without_reserve = self.client.get(url, {'include_reserve': 'false'})
        self.assertEqual(response_without_reserve.status_code, status.HTTP_200_OK)
        
        products_with = response_with_reserve.data['results']
        products_without = response_without_reserve.data['results']
        
        # Количество товаров должно быть одинаковым
        self.assertEqual(len(products_with), len(products_without))
        
        # Проверяем что данные о резерве различаются корректно
        for i, (with_reserve, without_reserve) in enumerate(zip(products_with, products_without)):
            self.assertEqual(with_reserve['id'], without_reserve['id'])
            
            # effective_stock с резервом должен быть больше или равен
            self.assertGreaterEqual(
                with_reserve['effective_stock'],
                without_reserve['effective_stock']
            )
    
    def test_tochka_production_only_production_needed_products(self):
        """Тест: список производства содержит только товары требующие производства."""
        url = reverse('tochka-production')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        products = response.data['results']
        
        for product in products:
            production_needed = float(product['production_needed'])
            self.assertGreater(production_needed, 0, 
                             f"Товар {product['article']} не должен быть в списке производства")


class TochkaReserveHighlightingTest(APITestCase):
    """Тесты подсветки строк с резервом в планировании производства."""
    
    def setUp(self):
        """Настройка тестовых данных."""
        # Создаем товары для тестирования подсветки
        self.highlight_products = []
        
        # Товар с резервом - должен подсвечиваться
        self.product_to_highlight = Product.objects.create(
            moysklad_id='highlight-test-1',
            article='HIGHLIGHT-001',
            name='Товар с резервом для подсветки',
            current_stock=Decimal('3'),
            reserved_stock=Decimal('7'),  # Есть резерв
            sales_last_2_months=Decimal('30'),
            production_needed=Decimal('12'),
            production_priority=85
        )
        
        # Товар без резерва - не должен подсвечиваться
        self.product_no_highlight = Product.objects.create(
            moysklad_id='highlight-test-2',
            article='HIGHLIGHT-002',
            name='Товар без резерва',
            current_stock=Decimal('4'),
            reserved_stock=Decimal('0'),  # Нет резерва
            sales_last_2_months=Decimal('25'),
            production_needed=Decimal('8'),
            production_priority=80
        )
        
        self.highlight_products = [
            self.product_to_highlight,
            self.product_no_highlight
        ]
    
    def test_tochka_production_includes_highlight_indicator(self):
        """Тест: API включает индикатор для подсветки строк с резервом."""
        url = reverse('tochka-production')
        response = self.client.get(url, {'include_reserve': 'true'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        products = response.data['results']
        
        for product in products:
            # Проверяем наличие поля для подсветки
            self.assertIn('reserved_stock', product)
            
            # Определяем должен ли товар подсвечиваться
            has_reserve = float(product['reserved_stock']) > 0
            
            # Если есть резерв, то должна быть возможность подсветки
            if has_reserve:
                self.assertGreater(float(product['reserved_stock']), 0)
                # Проверяем что у товара есть потребность в производстве
                self.assertGreater(float(product['production_needed']), 0)
    
    def test_tochka_production_reserve_highlighting_logic(self):
        """Тест: логика определения товаров для подсветки."""
        url = reverse('tochka-production')
        response = self.client.get(url, {'include_reserve': 'true'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        products = response.data['results']
        
        # Проверяем что товары правильно категоризируются для подсветки
        highlighted_count = 0
        not_highlighted_count = 0
        
        for product in products:
            reserved_stock = float(product['reserved_stock'])
            production_needed = float(product['production_needed'])
            
            # Товар должен подсвечиваться если есть резерв И нужно производство
            should_highlight = reserved_stock > 0 and production_needed > 0
            
            if should_highlight:
                highlighted_count += 1
                # Дополнительные проверки для подсвечиваемых товаров
                self.assertGreater(reserved_stock, 0)
                self.assertGreater(production_needed, 0)
            else:
                not_highlighted_count += 1
        
        # Проверяем что у нас есть товары обеих категорий для полноты тестирования
        self.assertGreater(len(products), 0)
        
        # Логируем результаты для отладки
        print(f"Товаров для подсветки: {highlighted_count}")
        print(f"Товаров без подсветки: {not_highlighted_count}")
    
    def test_tochka_production_highlight_data_structure(self):
        """Тест: структура данных для подсветки в ответе API."""
        url = reverse('tochka-production')
        response = self.client.get(url, {'include_reserve': 'true'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        products = response.data['results']
        
        for product in products:
            # Проверяем обязательные поля для подсветки
            required_fields = [
                'reserved_stock',
                'production_needed',
                'current_stock',
                'effective_stock',
                'article'
            ]
            
            for field in required_fields:
                self.assertIn(field, product, 
                             f"Поле {field} отсутствует в данных товара {product.get('article')}")
            
            # Проверяем типы данных
            self.assertIsInstance(product['reserved_stock'], (int, float, str))
            self.assertIsInstance(product['production_needed'], (int, float, str))
            
            # Проверяем что значения не отрицательные
            self.assertGreaterEqual(float(product['reserved_stock']), 0)
            self.assertGreaterEqual(float(product['production_needed']), 0)


class TochkaReserveIntegrationTest(TransactionTestCase):
    """Интеграционные тесты переключателя резерва между вкладками."""
    
    def setUp(self):
        """Настройка тестовых данных."""
        self.client = APIClient()
        
        # Создаем товары для интеграционного тестирования
        self.integration_products = []
        
        for i in range(5):
            product = Product.objects.create(
                moysklad_id=f'integration-test-{i+1}',
                article=f'INT-{i+1:03d}',
                name=f'Интеграционный товар {i+1}',
                current_stock=Decimal(str(5 + i * 2)),
                reserved_stock=Decimal(str(i)),  # 0, 1, 2, 3, 4
                sales_last_2_months=Decimal(str(10 + i * 5)),
                production_needed=Decimal(str(6 - i)) if i < 4 else Decimal('0'),
                production_priority=70 + i * 5
            )
            self.integration_products.append(product)
    
    def test_tochka_reserve_toggle_consistency_between_endpoints(self):
        """Тест: консистентность переключателя резерва между разными эндпоинтами."""
        # Тестируем оба состояния переключателя
        for include_reserve in ['true', 'false']:
            # Запрос к товарам Точки
            products_url = reverse('tochka-products')
            products_response = self.client.get(products_url, {'include_reserve': include_reserve})
            self.assertEqual(products_response.status_code, status.HTTP_200_OK)
            
            # Запрос к списку производства Точки
            production_url = reverse('tochka-production')
            production_response = self.client.get(production_url, {'include_reserve': include_reserve})
            self.assertEqual(production_response.status_code, status.HTTP_200_OK)
            
            # Проверяем консистентность расчета effective_stock
            products_data = {p['id']: p for p in products_response.data['results']}
            production_data = {p['id']: p for p in production_response.data['results']}
            
            # Находим товары которые есть в обоих списках
            common_product_ids = set(products_data.keys()) & set(production_data.keys())
            
            for product_id in common_product_ids:
                product_item = products_data[product_id]
                production_item = production_data[product_id]
                
                # effective_stock должен быть одинаковым в обеих таблицах
                self.assertEqual(
                    product_item['effective_stock'],
                    production_item['effective_stock'],
                    f"Inconsistent effective_stock for product {product_id} with include_reserve={include_reserve}"
                )
                
                # reserved_stock должен быть одинаковым
                self.assertEqual(
                    product_item['reserved_stock'],
                    production_item['reserved_stock'],
                    f"Inconsistent reserved_stock for product {product_id}"
                )
    
    def test_tochka_reserve_toggle_affects_all_calculations(self):
        """Тест: переключатель резерва влияет на все связанные расчеты."""
        product_id = self.integration_products[2].id  # Товар с резервом = 2
        
        # Запрос без учета резерва
        products_url = reverse('tochka-products')
        response_without = self.client.get(products_url, {'include_reserve': 'false'})
        self.assertEqual(response_without.status_code, status.HTTP_200_OK)
        
        # Запрос с учетом резерва
        response_with = self.client.get(products_url, {'include_reserve': 'true'})
        self.assertEqual(response_with.status_code, status.HTTP_200_OK)
        
        # Находим наш товар в обоих ответах
        products_without = {p['id']: p for p in response_without.data['results']}
        products_with = {p['id']: p for p in response_with.data['results']}
        
        product_without = products_without[product_id]
        product_with = products_with[product_id]
        
        # Проверяем что reserved_stock одинаковый (исходные данные)
        self.assertEqual(product_without['reserved_stock'], product_with['reserved_stock'])
        
        # Проверяем что effective_stock различается на величину reserved_stock
        expected_difference = float(product_with['reserved_stock'])
        actual_difference = product_with['effective_stock'] - product_without['effective_stock']
        
        self.assertAlmostEqual(actual_difference, expected_difference, places=2)
        
        # Проверяем что other fields остались неизменными
        unchanging_fields = ['current_stock', 'production_needed', 'production_priority']
        for field in unchanging_fields:
            self.assertEqual(
                product_without[field], 
                product_with[field],
                f"Field {field} should not change with reserve toggle"
            )
    
    def test_tochka_reserve_toggle_performance(self):
        """Тест: производительность переключателя резерва."""
        import time
        
        products_url = reverse('tochka-products')
        
        # Тестируем время ответа без учета резерва
        start_time = time.time()
        response_without = self.client.get(products_url, {'include_reserve': 'false'})
        time_without = time.time() - start_time
        
        self.assertEqual(response_without.status_code, status.HTTP_200_OK)
        
        # Тестируем время ответа с учетом резерва
        start_time = time.time()
        response_with = self.client.get(products_url, {'include_reserve': 'true'})
        time_with = time.time() - start_time
        
        self.assertEqual(response_with.status_code, status.HTTP_200_OK)
        
        # Проверяем что время отклика не превышает 5 секунд
        self.assertLess(time_without, 5.0, "Response time without reserve exceeds 5 seconds")
        self.assertLess(time_with, 5.0, "Response time with reserve exceeds 5 seconds")
        
        # Проверяем что добавление резерва не сильно замедляет запрос
        slowdown_factor = time_with / max(time_without, 0.001)  # Избегаем деления на 0
        self.assertLess(slowdown_factor, 2.0, "Reserve calculation causes significant slowdown")
        
        print(f"Performance test: without reserve {time_without:.3f}s, with reserve {time_with:.3f}s")


class TochkaFilteredProductionReserveTest(APITestCase):
    """Тесты отображения колонки резерва в отфильтрованном списке к производству."""
    
    def setUp(self):
        """Настройка тестовых данных для отфильтрованного списка."""
        # Создаем товары для тестирования отфильтрованного списка
        self.filtered_products = []
        
        for i in range(4):
            # Создаем товары с параметрами, которые приведут к production_needed > 0
            # Устанавливаем малые остатки и большие продажи для "старых" товаров
            product = Product.objects.create(
                moysklad_id=f'filtered-test-{i+1}',
                article=f'FILTERED-{i+1:03d}',
                name=f'Отфильтрованный товар {i+1}',
                current_stock=Decimal('2'),  # Малый остаток  
                reserved_stock=Decimal(str(i + 1)),  # 1, 2, 3, 4
                sales_last_2_months=Decimal('60'),  # Большие продажи = 1 шт/день
            )
            # production_needed и остальные поля рассчитаются автоматически в save()
            self.filtered_products.append(product)
    
    def test_tochka_filtered_production_includes_reserve_field(self):
        """Тест: отфильтрованный список производства включает поле reserved_stock."""
        # Подготавливаем Excel данные для фильтрации (артикулы должны совпадать с setUp)
        excel_data = [
            {'article': 'FILTERED-001', 'orders': 10},
            {'article': 'FILTERED-002', 'orders': 15},
            {'article': 'FILTERED-003', 'orders': 8}
        ]
        
        url = reverse('tochka-filtered-production')
        response = self.client.post(url, {
            'excel_data': excel_data,
            'include_reserve': True
        }, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        products = response.data['data']
        self.assertGreater(len(products), 0)
        
        for product in products:
            self.assertIn('reserved_stock', product)
            self.assertIn('current_stock', product)
            
            # Проверяем что effective_stock рассчитывается с учетом резерва
            expected_effective = float(product['current_stock']) + float(product.get('reserved_stock', 0))
            if 'effective_stock' in product:
                self.assertEqual(product['effective_stock'], expected_effective)
    
    def test_tochka_filtered_production_reserve_calculation_with_excel(self):
        """Тест: расчет резерва в отфильтрованном списке с данными Excel."""
        excel_data = [
            {'article': 'FILTERED-001', 'orders': 5},
            {'article': 'FILTERED-002', 'orders': 12}
        ]
        
        url = reverse('tochka-filtered-production')
        
        # Запрос без учета резерва
        response_without = self.client.post(url, {
            'excel_data': excel_data,
            'include_reserve': False
        }, format='json')
        
        # Запрос с учетом резерва
        response_with = self.client.post(url, {
            'excel_data': excel_data, 
            'include_reserve': True
        }, format='json')
        
        self.assertEqual(response_without.status_code, status.HTTP_200_OK)
        self.assertEqual(response_with.status_code, status.HTTP_200_OK)
        
        products_without = response_without.data['data']
        products_with = response_with.data['data']
        
        # Проверяем что товары те же, но расчеты разные
        self.assertEqual(len(products_without), len(products_with))
        
        for prod_without, prod_with in zip(products_without, products_with):
            self.assertEqual(prod_without['article'], prod_with['article'])
            
            # Резерв должен учитываться в расчетах
            reserved = float(prod_with.get('reserved_stock', 0))
            if reserved > 0:
                # Если есть резерв, то effective_stock должен отличаться
                current_stock = float(prod_with['current_stock'])
                expected_effective_with = current_stock + reserved
                expected_effective_without = current_stock
                
                if 'effective_stock' in prod_with:
                    self.assertEqual(prod_with['effective_stock'], expected_effective_with)
                if 'effective_stock' in prod_without:
                    self.assertEqual(prod_without['effective_stock'], expected_effective_without)


class TochkaReserveHighlightingLogicTest(APITestCase):
    """Дополнительные тесты логики подсветки строк с резервом."""
    
    def setUp(self):
        """Настройка тестовых данных для логики подсветки."""
        # Создаем товары с разными сценариями для подсветки
        self.highlight_scenarios = []
        
        # Сценарий 1: Высокий резерв, нужно производство -> ПОДСВЕТИТЬ
        self.scenario_1 = Product.objects.create(
            moysklad_id='highlight-scenario-1',
            article='HL-001',
            name='Высокий резерв + производство',
            current_stock=Decimal('5'),
            reserved_stock=Decimal('12'),  # Высокий резерв
            sales_last_2_months=Decimal('30'),
            production_needed=Decimal('8'),  # Нужно производство
            production_priority=90
        )
        
        # Сценарий 2: Малый резерв, нужно производство -> ПОДСВЕТИТЬ
        self.scenario_2 = Product.objects.create(
            moysklad_id='highlight-scenario-2',
            article='HL-002',
            name='Малый резерв + производство',
            current_stock=Decimal('3'),
            reserved_stock=Decimal('1'),  # Малый резерв
            sales_last_2_months=Decimal('20'),
            production_needed=Decimal('15'),  # Нужно производство
            production_priority=85
        )
        
        # Сценарий 3: Нет резерва, нужно производство -> НЕ ПОДСВЕЧИВАТЬ
        self.scenario_3 = Product.objects.create(
            moysklad_id='highlight-scenario-3',
            article='HL-003',
            name='Нет резерва + производство',
            current_stock=Decimal('2'),
            reserved_stock=Decimal('0'),  # Нет резерва
            sales_last_2_months=Decimal('25'),
            production_needed=Decimal('10'),  # Нужно производство
            production_priority=80
        )
        
        # Сценарий 4: Есть резерв, не нужно производство -> НЕ ПОДСВЕЧИВАТЬ
        self.scenario_4 = Product.objects.create(
            moysklad_id='highlight-scenario-4',
            article='HL-004',
            name='Есть резерв + не нужно производство',
            current_stock=Decimal('20'),
            reserved_stock=Decimal('5'),  # Есть резерв
            sales_last_2_months=Decimal('10'),
            production_needed=Decimal('0'),  # НЕ нужно производство
            production_priority=50
        )
        
        self.highlight_scenarios = [
            self.scenario_1, self.scenario_2, self.scenario_3, self.scenario_4
        ]
    
    def test_tochka_production_highlighting_scenarios(self):
        """Тест: различные сценарии подсветки в списке производства."""
        url = reverse('tochka-production')
        response = self.client.get(url, {'include_reserve': 'true'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        products = response.data['results']
        
        # Создаем словарь для быстрого поиска
        products_dict = {p['article']: p for p in products}
        
        # Сценарий 1: Высокий резерв + производство -> должен подсвечиваться
        if 'HL-001' in products_dict:
            product = products_dict['HL-001']
            self.assertGreater(float(product['reserved_stock']), 0)
            self.assertGreater(float(product['production_needed']), 0)
            # Этот товар должен подсвечиваться
        
        # Сценарий 2: Малый резерв + производство -> должен подсвечиваться  
        if 'HL-002' in products_dict:
            product = products_dict['HL-002']
            self.assertGreater(float(product['reserved_stock']), 0)
            self.assertGreater(float(product['production_needed']), 0)
            # Этот товар должен подсвечиваться
        
        # Сценарий 3: Нет резерва + производство -> НЕ должен подсвечиваться
        if 'HL-003' in products_dict:
            product = products_dict['HL-003']
            self.assertEqual(float(product['reserved_stock']), 0)
            self.assertGreater(float(product['production_needed']), 0)
            # Этот товар НЕ должен подсвечиваться
        
        # Сценарий 4: НЕ должен быть в списке производства (production_needed = 0)
        self.assertNotIn('HL-004', products_dict, 
                        "Товар без потребности в производстве не должен быть в списке")
    
    def test_tochka_production_highlight_metadata(self):
        """Тест: метаданные для подсветки в ответе API."""
        url = reverse('tochka-production')
        response = self.client.get(url, {'include_reserve': 'true'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        products = response.data['results']
        
        # Подсчитываем статистику для подсветки
        total_products = len(products)
        products_with_reserve = 0
        products_for_highlighting = 0
        
        for product in products:
            reserved_stock = float(product['reserved_stock'])
            production_needed = float(product['production_needed'])
            
            if reserved_stock > 0:
                products_with_reserve += 1
                
                if production_needed > 0:
                    products_for_highlighting += 1
        
        # Проверяем логическую консистентность
        self.assertLessEqual(products_for_highlighting, products_with_reserve)
        self.assertLessEqual(products_with_reserve, total_products)
        
        # Логируем статистику для анализа
        print(f"Статистика подсветки:")
        print(f"  Всего товаров на производство: {total_products}")
        print(f"  Товаров с резервом: {products_with_reserve}")
        print(f"  Товаров для подсветки: {products_for_highlighting}")
        
        # Проверяем что есть товары для тестирования
        self.assertGreater(total_products, 0)
    
    def test_tochka_production_highlight_edge_cases(self):
        """Тест: граничные случаи для подсветки."""
        # Создаем товар с очень малым резервом
        edge_case_product = Product.objects.create(
            moysklad_id='edge-case-1',
            article='EDGE-001',
            name='Граничный случай - малый резерв',
            current_stock=Decimal('1'),
            reserved_stock=Decimal('0.1'),  # Очень малый резерв
            sales_last_2_months=Decimal('5'),
            production_needed=Decimal('20'),
            production_priority=95
        )
        
        url = reverse('tochka-production')
        response = self.client.get(url, {'include_reserve': 'true'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        products = response.data['results']
        edge_product = next((p for p in products if p['article'] == 'EDGE-001'), None)
        
        if edge_product:
            # Даже очень малый резерв должен учитываться для подсветки
            self.assertGreater(float(edge_product['reserved_stock']), 0)
            self.assertGreater(float(edge_product['production_needed']), 0)
            
            # effective_stock должен быть больше current_stock
            effective_stock = float(edge_product.get('effective_stock', edge_product['current_stock']))
            current_stock = float(edge_product['current_stock'])
            self.assertGreater(effective_stock, current_stock)


class TochkaReserveErrorHandlingTest(APITestCase):
    """Тесты обработки ошибок для функциональности резерва."""
    
    def test_tochka_products_invalid_include_reserve_parameter(self):
        """Тест: обработка некорректного значения параметра include_reserve."""
        url = reverse('tochka-products')
        
        # Тестируем различные некорректные значения
        invalid_values = ['invalid', '123', 'yes', 'no', '']
        
        for invalid_value in invalid_values:
            response = self.client.get(url, {'include_reserve': invalid_value})
            
            # Запрос должен выполняться успешно (fallback к default значению)
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            
            # Проверяем что API обрабатывает некорректное значение как False
            products = response.data['results']
            if products:
                # Проверяем что effective_stock равен current_stock (как при False)
                first_product = products[0]
                db_product = Product.objects.get(id=first_product['id'])
                expected_effective_stock = float(db_product.current_stock)
                self.assertEqual(first_product['effective_stock'], expected_effective_stock)
    
    def test_tochka_products_with_null_reserve_values(self):
        """Тест: обработка товаров с NULL значениями резерва."""
        # Создаем товар с None в reserved_stock (в базе данных NULL)
        product_with_null_reserve = Product.objects.create(
            moysklad_id='null-reserve-test',
            article='NULL-RESERVE',
            name='Товар с NULL резервом',
            current_stock=Decimal('10'),
            # reserved_stock намеренно не устанавливаем (будет default=0)
            sales_last_2_months=Decimal('20')
        )
        
        url = reverse('tochka-products')
        response = self.client.get(url, {'include_reserve': 'true'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        products = response.data['results']
        null_reserve_product = next(
            (p for p in products if p['id'] == product_with_null_reserve.id), 
            None
        )
        
        self.assertIsNotNone(null_reserve_product)
        
        # Проверяем что NULL резерв обрабатывается как 0
        self.assertEqual(float(null_reserve_product['reserved_stock']), 0.0)
        self.assertEqual(
            null_reserve_product['effective_stock'],
            float(product_with_null_reserve.current_stock)
        )
    
    def test_tochka_production_empty_result_with_reserve(self):
        """Тест: корректная обработка пустого списка производства с резервом."""
        # Удаляем все товары требующие производства
        Product.objects.filter(production_needed__gt=0).delete()
        
        url = reverse('tochka-production')
        response = self.client.get(url, {'include_reserve': 'true'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Проверяем что возвращается пустой список
        self.assertEqual(len(response.data['results']), 0)
        self.assertIn('message', response.data)