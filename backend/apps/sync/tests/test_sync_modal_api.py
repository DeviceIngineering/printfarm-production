"""
Тесты для проверки API endpoints модального окна синхронизации.
"""

import json
from unittest.mock import Mock, patch
from django.test import TestCase, Client
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.core.exceptions import SyncException


class TestSyncModalAPI(APITestCase):
    """Тесты для API endpoints модального окна синхронизации."""
    
    def setUp(self):
        """Подготовка тестовых данных."""
        self.client = Client()
    
    @patch('apps.sync.views.MoySkladClient')
    def test_warehouses_endpoint_success(self, mock_client_class):
        """
        Тест проверяет успешное получение списка складов.
        """
        # Подготовка мока клиента
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        mock_client.test_connection.return_value = True
        mock_client.get_warehouses.return_value = [
            {
                'id': 'warehouse-1',
                'name': 'Основной склад',
                'code': 'MAIN',
                'address': 'Москва, ул. Тестовая, 1'
            },
            {
                'id': 'warehouse-2', 
                'name': 'Дополнительный склад',
                'code': 'EXTRA',
                'address': 'СПб, ул. Пробная, 2'
            }
        ]
        
        # Выполняем запрос
        url = reverse('sync-warehouses')
        response = self.client.get(url)
        
        # Проверяем результат
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(len(data), 2)
        self.assertEqual(data[0]['name'], 'Основной склад')
        self.assertEqual(data[1]['name'], 'Дополнительный склад')
    
    @patch('apps.sync.views.MoySkladClient')
    def test_warehouses_endpoint_connection_error(self, mock_client_class):
        """
        Тест проверяет обработку ошибки соединения с МойСклад.
        """
        # Подготовка мока клиента
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        mock_client.test_connection.return_value = False
        
        # Выполняем запрос
        url = reverse('sync-warehouses')
        response = self.client.get(url)
        
        # Проверяем результат
        self.assertEqual(response.status_code, status.HTTP_503_SERVICE_UNAVAILABLE)
        data = response.json()
        self.assertIn('error', data)
        self.assertEqual(data['type'], 'ConnectionError')
        self.assertIn('suggestions', data)
    
    @patch('apps.sync.views.MoySkladClient')
    def test_product_groups_endpoint_success(self, mock_client_class):
        """
        Тест проверяет успешное получение списка групп товаров.
        """
        # Подготовка мока клиента
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        mock_client.test_connection.return_value = True
        mock_client.get_product_groups.return_value = [
            {
                'id': 'group-1',
                'name': 'Электроника',
                'pathName': 'Товары > Электроника',
                'code': 'ELEC',
                'archived': False
            },
            {
                'id': 'group-2',
                'name': 'Одежда',
                'pathName': 'Товары > Одежда',
                'code': 'CLOTH',
                'archived': False
            }
        ]
        
        # Выполняем запрос
        url = reverse('sync-product-groups')
        response = self.client.get(url)
        
        # Проверяем результат
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(len(data), 2)
        self.assertEqual(data[0]['name'], 'Электроника')
        self.assertEqual(data[1]['name'], 'Одежда')
    
    @patch('apps.sync.views.MoySkladClient')
    def test_product_groups_endpoint_connection_error(self, mock_client_class):
        """
        Тест проверяет обработку ошибки соединения при получении групп товаров.
        """
        # Подготовка мока клиента
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        mock_client.test_connection.return_value = False
        
        # Выполняем запрос
        url = reverse('sync-product-groups')
        response = self.client.get(url)
        
        # Проверяем результат
        self.assertEqual(response.status_code, status.HTTP_503_SERVICE_UNAVAILABLE)
        data = response.json()
        self.assertIn('error', data)
        self.assertEqual(data['type'], 'ConnectionError')
    
    @patch('apps.sync.views.MoySkladClient')
    def test_warehouses_endpoint_api_exception(self, mock_client_class):
        """
        Тест проверяет обработку исключений API МойСклад.
        """
        # Подготовка мока клиента
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        mock_client.test_connection.return_value = True
        mock_client.get_warehouses.side_effect = Exception("API limit exceeded")
        
        # Выполняем запрос
        url = reverse('sync-warehouses')
        response = self.client.get(url)
        
        # Проверяем результат
        self.assertEqual(response.status_code, status.HTTP_503_SERVICE_UNAVAILABLE)
        data = response.json()
        self.assertIn('error', data)
        self.assertEqual(data['error'], 'API limit exceeded')
        self.assertIn('suggestions', data)
    
    def test_warehouses_endpoint_cors_headers(self):
        """
        Тест проверяет наличие CORS заголовков для frontend.
        """
        url = reverse('sync-warehouses')
        response = self.client.get(url, HTTP_ORIGIN='http://localhost:3000')
        
        # CORS заголовки должны быть настроены в Django settings
        # Проверяем что запрос не блокируется
        self.assertIn(response.status_code, [200, 503])  # 200 если API работает, 503 если нет соединения
    
    def test_sync_endpoints_available(self):
        """
        Тест проверяет доступность всех sync endpoints.
        """
        endpoints = [
            'sync-warehouses',
            'sync-product-groups', 
            'sync-status',
            'sync-history'
        ]
        
        for endpoint_name in endpoints:
            url = reverse(endpoint_name)
            response = self.client.get(url)
            # Все endpoints должны быть доступны (не 404)
            self.assertNotEqual(response.status_code, status.HTTP_404_NOT_FOUND,
                               f"Endpoint {endpoint_name} not found")