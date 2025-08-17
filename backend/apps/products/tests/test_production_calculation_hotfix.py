"""
Регрессионные тесты для hotfix production calculation API
"""
from django.test import TestCase
from rest_framework.test import APITestCase
from rest_framework import status
from apps.products.models import Product
from apps.sync.models import ProductionList


class ProductionCalculationHotfixTests(APITestCase):
    """
    Регрессионные тесты для исправления проблемы с расчетом списка производства
    """
    
    def setUp(self):
        # Создаем тестовые товары для расчета производства
        self.test_products = []
        for i in range(5):
            product = Product.objects.create(
                moysklad_id=f'test-{i}',
                article=f'TEST-{i:03d}',
                name=f'Тестовый товар {i}',
                current_stock=i * 2,
                production_needed=10 + i,
                production_priority=80 - i * 10
            )
            self.test_products.append(product)
    
    def test_calculate_production_list_api_returns_success(self):
        """
        Тест: API /api/v1/products/production/calculate/ возвращает успешный ответ
        """
        response = self.client.post('/api/v1/products/production/calculate/', {
            'min_priority': 20,
            'apply_coefficients': True
        }, format='json')
        
        # Проверяем успешный статус
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Проверяем структуру ответа
        self.assertIn('message', response.data)
        self.assertIn('production_list_id', response.data)
        self.assertIn('total_items', response.data)
        self.assertIn('total_units', response.data)
        
        # Проверяем, что создался список производства
        production_list_id = response.data['production_list_id']
        production_list = ProductionList.objects.get(id=production_list_id)
        self.assertIsNotNone(production_list)
    
    def test_calculate_production_list_with_empty_params(self):
        """
        Тест: API работает с пустыми параметрами (значения по умолчанию)
        """
        response = self.client.post('/api/v1/products/production/calculate/', {}, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('message', response.data)
        self.assertEqual(response.data['message'], 'Production list calculated successfully')
    
    def test_calculate_production_list_no_circular_import_error(self):
        """
        Тест: Отсутствие ошибки циклического импорта
        """
        response = self.client.post('/api/v1/products/production/calculate/', {}, format='json')
        
        # Главная проверка - отсутствие ошибки импорта
        self.assertNotEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        # Проверяем, что ответ не содержит ошибку импорта
        if 'error' in response.data:
            self.assertNotIn('cannot import', response.data['error'].lower())
            self.assertNotIn('productionservice', response.data['error'].lower())
    
    def test_get_production_list_api_works(self):
        """
        Тест: API /api/v1/products/production/list/ работает корректно
        """
        # Сначала создаем список производства
        calculate_response = self.client.post('/api/v1/products/production/calculate/', {}, format='json')
        self.assertEqual(calculate_response.status_code, status.HTTP_201_CREATED)
        
        # Затем получаем список
        response = self.client.get('/api/v1/products/production/list/')
        
        # Проверяем успешность
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Проверяем структуру ответа
        self.assertIn('id', response.data)
        self.assertIn('total_items', response.data)
        self.assertIn('total_units', response.data)
        self.assertIn('items', response.data)
    
    def test_production_service_inline_class_functional(self):
        """
        Тест: Inline ProductionService класс функционален
        """
        # Проверяем, что можно создать список производства без ошибок импорта
        initial_count = ProductionList.objects.count()
        
        response = self.client.post('/api/v1/products/production/calculate/', {
            'min_priority': 50,
            'apply_coefficients': False
        }, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Проверяем, что создался новый список
        final_count = ProductionList.objects.count()
        self.assertEqual(final_count, initial_count + 1)
    
    def test_production_calculation_with_various_priorities(self):
        """
        Тест: Расчет работает с различными значениями min_priority
        """
        test_priorities = [0, 20, 50, 80, 100]
        
        for priority in test_priorities:
            with self.subTest(priority=priority):
                response = self.client.post('/api/v1/products/production/calculate/', {
                    'min_priority': priority,
                    'apply_coefficients': True
                }, format='json')
                
                self.assertEqual(response.status_code, status.HTTP_201_CREATED)
                self.assertIn('total_items', response.data)
                
                # Проверяем, что total_items соответствует количеству товаров с нужным приоритетом
                expected_items = Product.objects.filter(
                    production_needed__gt=0,
                    production_priority__gte=priority
                ).count()
                self.assertEqual(response.data['total_items'], expected_items)
    
    def test_api_error_handling_robust(self):
        """
        Тест: Обработка ошибок API не вызывает internal server errors
        """
        # Тестируем различные некорректные запросы
        test_cases = [
            {'min_priority': 'invalid'},  # Некорректный тип
            {'min_priority': -1},         # Отрицательное значение
            {'apply_coefficients': 'not_boolean'},  # Некорректный boolean
        ]
        
        for test_case in test_cases:
            with self.subTest(params=test_case):
                response = self.client.post('/api/v1/products/production/calculate/', test_case, format='json')
                
                # Не должно быть 500 ошибки, максимум 400 (Bad Request)
                self.assertNotEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def test_no_regression_message_error_from_frontend_button(self):
        """
        Тест: Отсутствие регрессии "ошибка расчета списка производства" 
        """
        # Симулируем точно такой же запрос, какой делает frontend кнопка
        response = self.client.post('/api/v1/products/production/calculate/', {
            'min_priority': 20,
            'apply_coefficients': True
        }, format='json')
        
        # Основная проверка - нет ошибки
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Проверяем, что сообщение об успехе корректное
        self.assertEqual(response.data['message'], 'Production list calculated successfully')
        
        # Проверяем, что есть ID созданного списка
        self.assertIsInstance(response.data['production_list_id'], int)
        self.assertGreater(response.data['production_list_id'], 0)


class ProductionServiceImportTests(TestCase):
    """
    Тесты для проверки отсутствия проблем с импортом ProductionService
    """
    
    def test_no_circular_import_in_views(self):
        """
        Тест: Отсутствие циклического импорта в views.py
        """
        try:
            # Пытаемся импортировать views модуль
            from apps.products import views
            self.assertTrue(True, "Views module imported successfully")
        except ImportError as e:
            self.fail(f"Circular import detected: {e}")
    
    def test_inline_production_service_class_exists(self):
        """
        Тест: Inline ProductionService класс создается корректно
        """
        # Этот тест проверяет, что inline класс в views.py работает
        from django.test import RequestFactory
        from apps.products.views import calculate_production_list
        
        factory = RequestFactory()
        request = factory.post('/api/v1/products/production/calculate/', {})
        request.data = {'min_priority': 20, 'apply_coefficients': True}
        
        # Если функция выполняется без ImportError, значит все ОК
        try:
            response = calculate_production_list(request)
            self.assertIsNotNone(response)
        except ImportError as e:
            self.fail(f"Import error in production calculation: {e}")