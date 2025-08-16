"""
Тесты для нового алгоритма расчета резерва в колонке "Резерв"
на вкладке Точка в таблице "Список к производству"

Алгоритм:
- Если Резерв > 0: отображать (Резерв - Остаток)
- Цветовая индикация:
  - Синий: если Резерв > Остаток  
  - Красный: если Резерв <= Остаток

Бизнес-цель: Сделать значения в колонке Резерв более значимыми 
и удобными для чтения пользователем
"""

import unittest
from decimal import Decimal
from django.test import TestCase
from apps.products.models import Product
from apps.products.services.reserve_calculator import ReserveCalculatorService


class ReserveCalculationAlgorithmTest(TestCase):
    """
    Тестирование нового алгоритма расчета резерва
    """
    
    def setUp(self):
        """Подготовка тестовых данных"""
        self.calculator = ReserveCalculatorService()
        
    def test_reserve_calculation_when_reserve_greater_than_stock(self):
        """
        Тест: Резерв больше остатка (синий цвет)
        Резерв = 15, Остаток = 10
        Ожидаемый результат: calculated_reserve = 5, color = "blue"
        """
        result = self.calculator.calculate_reserve_display(
            reserved_stock=Decimal('15'),
            current_stock=Decimal('10')
        )
        
        self.assertEqual(result['calculated_reserve'], Decimal('5'))
        self.assertEqual(result['color_indicator'], 'blue')
        self.assertTrue(result['is_positive'])
        
    def test_reserve_calculation_when_reserve_equals_stock(self):
        """
        Тест: Резерв равен остатку (красный цвет)
        Резерв = 10, Остаток = 10
        Ожидаемый результат: calculated_reserve = 0, color = "red"
        """
        result = self.calculator.calculate_reserve_display(
            reserved_stock=Decimal('10'),
            current_stock=Decimal('10')
        )
        
        self.assertEqual(result['calculated_reserve'], Decimal('0'))
        self.assertEqual(result['color_indicator'], 'red')
        self.assertFalse(result['is_positive'])
        
    def test_reserve_calculation_when_reserve_less_than_stock(self):
        """
        Тест: Резерв меньше остатка (красный цвет)
        Резерв = 5, Остаток = 10
        Ожидаемый результат: calculated_reserve = -5, color = "red"
        """
        result = self.calculator.calculate_reserve_display(
            reserved_stock=Decimal('5'),
            current_stock=Decimal('10')
        )
        
        self.assertEqual(result['calculated_reserve'], Decimal('-5'))
        self.assertEqual(result['color_indicator'], 'red')
        self.assertFalse(result['is_positive'])
        
    def test_reserve_calculation_when_no_reserve(self):
        """
        Тест: Резерв равен нулю
        Резерв = 0, Остаток = 10
        Ожидаемый результат: не показывать расчет (original_reserve = 0)
        """
        result = self.calculator.calculate_reserve_display(
            reserved_stock=Decimal('0'),
            current_stock=Decimal('10')
        )
        
        self.assertEqual(result['calculated_reserve'], Decimal('-10'))  # 0 - 10 = -10
        self.assertEqual(result['color_indicator'], 'gray')
        self.assertFalse(result['should_show_calculation'])
        
    def test_reserve_calculation_edge_cases(self):
        """
        Тест: Граничные случаи
        """
        # Большие числа
        result = self.calculator.calculate_reserve_display(
            reserved_stock=Decimal('1000'),
            current_stock=Decimal('999')
        )
        self.assertEqual(result['calculated_reserve'], Decimal('1'))
        self.assertEqual(result['color_indicator'], 'blue')
        
        # Десятичные числа
        result = self.calculator.calculate_reserve_display(
            reserved_stock=Decimal('10.5'),
            current_stock=Decimal('10.2')
        )
        self.assertEqual(result['calculated_reserve'], Decimal('0.3'))
        self.assertEqual(result['color_indicator'], 'blue')
        
    def test_performance_requirement(self):
        """
        Тест: Производительность расчета должна быть < 5 сек для 1000 товаров
        """
        import time
        
        start_time = time.time()
        
        # Тестируем на 1000 вычислений
        for i in range(1000):
            self.calculator.calculate_reserve_display(
                reserved_stock=Decimal(str(i + 10)),
                current_stock=Decimal(str(i + 5))
            )
            
        end_time = time.time()
        execution_time = end_time - start_time
        
        # Требование: менее 5 секунд
        self.assertLess(execution_time, 5.0, 
                       f"Время выполнения {execution_time:.2f} сек превышает лимит 5 сек")


class ProductReserveIntegrationTest(TestCase):
    """
    Интеграционные тесты для работы с моделью Product
    """
    
    def setUp(self):
        """Создание тестовых товаров"""
        self.product1 = Product.objects.create(
            moysklad_id="test-product-1",
            article="TEST-001",
            name="Тестовый товар 1",
            current_stock=Decimal('10'),
            reserved_stock=Decimal('15'),
            production_needed=Decimal('5'),
            production_priority=80
        )
        
        self.product2 = Product.objects.create(
            moysklad_id="test-product-2", 
            article="TEST-002",
            name="Тестовый товар 2",
            current_stock=Decimal('20'),
            reserved_stock=Decimal('15'),
            production_needed=Decimal('10'),
            production_priority=60
        )
        
        self.calculator = ReserveCalculatorService()
        
    def test_product_reserve_calculation_integration(self):
        """
        Интеграционный тест: расчет резерва для товаров из БД
        """
        # Товар 1: Резерв больше остатка (синий)
        result1 = self.calculator.calculate_reserve_display(
            reserved_stock=self.product1.reserved_stock,
            current_stock=self.product1.current_stock
        )
        
        self.assertEqual(result1['calculated_reserve'], Decimal('5'))
        self.assertEqual(result1['color_indicator'], 'blue')
        
        # Товар 2: Резерв меньше остатка (красный)
        result2 = self.calculator.calculate_reserve_display(
            reserved_stock=self.product2.reserved_stock,
            current_stock=self.product2.current_stock
        )
        
        self.assertEqual(result2['calculated_reserve'], Decimal('-5'))
        self.assertEqual(result2['color_indicator'], 'red')
        
    def test_production_list_with_reserve_calculation(self):
        """
        Тест: Список к производству с расчетом резерва
        """
        products_for_production = Product.objects.filter(
            production_needed__gt=0
        ).order_by('-production_priority')
        
        results = []
        for product in products_for_production:
            reserve_calc = self.calculator.calculate_reserve_display(
                reserved_stock=product.reserved_stock,
                current_stock=product.current_stock
            )
            
            results.append({
                'article': product.article,
                'name': product.name,
                'current_stock': product.current_stock,
                'reserved_stock': product.reserved_stock,
                'calculated_reserve': reserve_calc['calculated_reserve'],
                'color_indicator': reserve_calc['color_indicator'],
                'production_needed': product.production_needed,
                'production_priority': product.production_priority
            })
            
        # Проверяем, что результаты получены
        self.assertEqual(len(results), 2)
        
        # Проверяем сортировку по приоритету
        self.assertEqual(results[0]['article'], 'TEST-001')  # Приоритет 80
        self.assertEqual(results[1]['article'], 'TEST-002')  # Приоритет 60
        
        # Проверяем расчеты резерва
        self.assertEqual(results[0]['calculated_reserve'], Decimal('5'))
        self.assertEqual(results[0]['color_indicator'], 'blue')
        
        self.assertEqual(results[1]['calculated_reserve'], Decimal('-5'))
        self.assertEqual(results[1]['color_indicator'], 'red')


class BackwardCompatibilityTest(TestCase):
    """
    Тесты обратной совместимости
    """
    
    def test_existing_reserved_stock_field(self):
        """
        Тест: Существующее поле reserved_stock работает без изменений
        """
        product = Product.objects.create(
            moysklad_id="test-compat-1",
            article="COMPAT-001",
            name="Совместимость тест",
            reserved_stock=Decimal('25')
        )
        
        # Поле должно сохраняться как раньше
        self.assertEqual(product.reserved_stock, Decimal('25'))
        
        # Новый расчет не должен влиять на хранимое значение
        calculator = ReserveCalculatorService()
        result = calculator.calculate_reserve_display(
            reserved_stock=product.reserved_stock,
            current_stock=Decimal('20')
        )
        
        # Исходное значение не изменилось
        product.refresh_from_db()
        self.assertEqual(product.reserved_stock, Decimal('25'))
        
        # Но новый расчет работает
        self.assertEqual(result['calculated_reserve'], Decimal('5'))


if __name__ == '__main__':
    unittest.main()