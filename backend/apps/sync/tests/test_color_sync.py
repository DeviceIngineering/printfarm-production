"""
Тесты для проверки синхронизации цвета товаров из МойСклад.
"""

import json
from datetime import datetime, timedelta
from decimal import Decimal
from unittest.mock import Mock, patch, MagicMock
from django.test import TestCase
from django.utils import timezone

from apps.products.models import Product
from apps.sync.models import SyncLog
from apps.sync.services import SyncService


class TestColorSync(TestCase):
    """Тесты для проверки корректной синхронизации цвета товаров."""
    
    def setUp(self):
        """Подготовка тестовых данных."""
        self.sync_service = SyncService()
        self.warehouse_id = 'test-warehouse-id'
    
    @patch('apps.sync.services.MoySkladClient')
    def test_color_saved_during_sync(self, mock_client_class):
        """
        Тест проверяет, что цвет товара сохраняется во время синхронизации.
        
        Проблема была в том, что product.save() находился внутри блока except,
        и товар не сохранялся если не было ошибки при получении цвета.
        """
        # Подготовка мока клиента
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        # Мокаем данные товаров с атрибутами цвета
        mock_products_data = [
            {
                'meta': {'href': 'https://api.moysklad.ru/api/remap/1.2/entity/product/test-id-1'},
                'name': 'Тестовый товар 1',
                'article': 'TEST001',
                'stock': 10,
                'quantity': 10,
                'attributes': [
                    {
                        'meta': {'type': 'attributemetadata', 'href': 'https://.../цвет'},
                        'value': 'Красный'
                    }
                ]
            },
            {
                'meta': {'href': 'https://api.moysklad.ru/api/remap/1.2/entity/product/test-id-2'},
                'name': 'Тестовый товар 2',
                'article': 'TEST002',
                'stock': 5,
                'quantity': 5,
                'attributes': [
                    {
                        'name': 'Цвет',
                        'value': {'name': 'Синий'}  # CustomEntity формат
                    }
                ]
            }
        ]
        
        mock_client.get_all_products_with_stock.return_value = mock_products_data
        mock_client.get_turnover_report.return_value = []
        mock_client.extract_color_from_attributes.side_effect = ['Красный', 'Синий']
        
        # Выполняем синхронизацию
        sync_log = self.sync_service.sync_products(
            warehouse_id=self.warehouse_id,
            sync_type='manual',
            sync_images=False
        )
        
        # Проверяем результаты
        self.assertEqual(sync_log.status, 'success')
        self.assertEqual(Product.objects.count(), 2)
        
        # Проверяем что цвета сохранены
        product1 = Product.objects.get(article='TEST001')
        self.assertEqual(product1.color, 'Красный')
        
        product2 = Product.objects.get(article='TEST002')
        self.assertEqual(product2.color, 'Синий')
    
    def test_extract_color_from_different_formats(self):
        """Тест проверяет извлечение цвета из разных форматов атрибутов."""
        from apps.sync.moysklad_client import MoySkladClient
        
        client = MoySkladClient()
        
        # Формат 1: Атрибут с meta и простым значением
        attributes1 = [
            {
                'meta': {'type': 'attributemetadata', 'href': 'https://api/attr/цвет'},
                'value': 'Зеленый'
            }
        ]
        color1 = client.extract_color_from_attributes(attributes1)
        self.assertEqual(color1, 'Зеленый')
        
        # Формат 2: Атрибут с name и customEntity значением
        attributes2 = [
            {
                'name': 'Цвет',
                'value': {'name': 'Желтый'}
            }
        ]
        color2 = client.extract_color_from_attributes(attributes2)
        self.assertEqual(color2, 'Желтый')
        
        # Формат 3: Атрибут с name и простым строковым значением
        attributes3 = [
            {
                'name': 'Цвет',
                'value': 'Белый'
            }
        ]
        color3 = client.extract_color_from_attributes(attributes3)
        self.assertEqual(color3, 'Белый')
        
        # Формат 4: Пустые атрибуты
        attributes4 = []
        color4 = client.extract_color_from_attributes(attributes4)
        self.assertEqual(color4, '')
        
        # Формат 5: Атрибуты без цвета
        attributes5 = [
            {
                'name': 'Размер',
                'value': 'XL'
            }
        ]
        color5 = client.extract_color_from_attributes(attributes5)
        self.assertEqual(color5, '')
    
    @patch('apps.sync.services.MoySkladClient')
    def test_color_saved_even_with_error(self, mock_client_class):
        """
        Тест проверяет, что товар сохраняется даже если произошла ошибка
        при извлечении цвета.
        """
        # Подготовка мока клиента
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        # Мокаем данные товаров
        mock_products_data = [
            {
                'meta': {'href': 'https://api.moysklad.ru/api/remap/1.2/entity/product/test-id-3'},
                'name': 'Тестовый товар 3',
                'article': 'TEST003',
                'stock': 15,
                'quantity': 15,
                'attributes': [{'broken': 'attribute'}]  # Некорректный атрибут
            }
        ]
        
        mock_client.get_all_products_with_stock.return_value = mock_products_data
        mock_client.get_turnover_report.return_value = []
        mock_client.extract_color_from_attributes.side_effect = Exception("Ошибка парсинга")
        
        # Выполняем синхронизацию
        sync_log = self.sync_service.sync_products(
            warehouse_id=self.warehouse_id,
            sync_type='manual',
            sync_images=False
        )
        
        # Проверяем что товар сохранен несмотря на ошибку
        self.assertEqual(sync_log.status, 'success')
        self.assertEqual(Product.objects.count(), 1)
        
        product = Product.objects.get(article='TEST003')
        self.assertEqual(product.color, '')  # Цвет пустой из-за ошибки
        self.assertEqual(product.current_stock, Decimal('15'))  # Но остальные данные сохранены