"""
Регрессионные тесты для hotfix прогресса синхронизации
"""
import time
from unittest.mock import Mock, patch
from django.test import TestCase
from rest_framework.test import APITestCase
from rest_framework import status
from apps.sync.models import SyncLog
from apps.sync.services import SyncService


class SyncProgressHotfixTests(APITestCase):
    """
    Регрессионные тесты для исправления отображения прогресса синхронизации
    """
    
    def test_sync_status_api_returns_progress_data(self):
        """
        Тест: API /api/v1/sync/status/ возвращает корректные данные прогресса
        """
        # Создаем активную синхронизацию
        sync_log = SyncLog.objects.create(
            sync_type='manual',
            status='pending',
            warehouse_id='test-warehouse',
            warehouse_name='Test Warehouse',
            total_products=100,
            synced_products=25,
            current_article='TEST-123'
        )
        
        response = self.client.get('/api/v1/sync/status/')
        
        # Проверяем успешный статус
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Проверяем структуру ответа
        self.assertIn('is_syncing', response.data)
        self.assertIn('sync_id', response.data)
        self.assertIn('total_products', response.data)
        self.assertIn('synced_products', response.data)
        self.assertIn('current_article', response.data)
        
        # Проверяем корректные значения
        self.assertTrue(response.data['is_syncing'])
        self.assertEqual(response.data['sync_id'], sync_log.id)
        self.assertEqual(response.data['total_products'], 100)
        self.assertEqual(response.data['synced_products'], 25)
        self.assertEqual(response.data['current_article'], 'TEST-123')
    
    def test_sync_status_api_returns_zero_when_no_progress(self):
        """
        Тест: API возвращает 0 когда синхронизация еще не начата
        """
        # Создаем синхронизацию без прогресса
        sync_log = SyncLog.objects.create(
            sync_type='manual',
            status='pending',
            warehouse_id='test-warehouse',
            warehouse_name='Test Warehouse',
            total_products=0,
            synced_products=0
        )
        
        response = self.client.get('/api/v1/sync/status/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['total_products'], 0)
        self.assertEqual(response.data['synced_products'], 0)
    
    def test_sync_status_api_when_no_active_sync(self):
        """
        Тест: API корректно обрабатывает ситуацию когда нет активной синхронизации
        """
        response = self.client.get('/api/v1/sync/status/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data['is_syncing'])
        self.assertIn('last_sync', response.data)
        
    def test_no_regression_zero_progress_display(self):
        """
        Тест: Отсутствие регрессии "Обработано: 0 из 0 товаров"
        """
        # Симулируем реальную синхронизацию с прогрессом
        sync_log = SyncLog.objects.create(
            sync_type='manual',
            status='pending',
            warehouse_id='test-warehouse',
            warehouse_name='Test Warehouse',
            total_products=250,
            synced_products=75,
            current_article='REAL-ARTICLE-456'
        )
        
        response = self.client.get('/api/v1/sync/status/')
        
        # Главная проверка - прогресс НЕ равен "0 из 0"
        self.assertNotEqual(response.data['total_products'], 0)
        self.assertNotEqual(response.data['synced_products'], 0)
        
        # Проверяем реальные значения
        self.assertEqual(response.data['total_products'], 250)
        self.assertEqual(response.data['synced_products'], 75)
        self.assertEqual(response.data['current_article'], 'REAL-ARTICLE-456')


class SyncServiceProgressTests(TestCase):
    """
    Тесты для проверки обновления прогресса в SyncService
    """
    
    @patch('apps.sync.services.MoySkladClient')
    def test_sync_service_updates_progress_during_processing(self, mock_client_class):
        """
        Тест: SyncService обновляет прогресс во время обработки
        """
        # Создаем мок экземпляра клиента
        mock_client_instance = Mock()
        mock_client_class.return_value = mock_client_instance
        
        # Мокаем данные клиента
        mock_client_instance.get_warehouses.return_value = [
            {'id': 'test-warehouse', 'name': 'Test Warehouse'}
        ]
        mock_client_instance.get_all_products_with_stock.return_value = [
            {
                'meta': {'type': 'product', 'href': 'http://test.com/product/1'},
                'article': 'TEST-001',
                'name': 'Test Product 1',
                'stock': 10
            },
            {
                'meta': {'type': 'product', 'href': 'http://test.com/product/2'},
                'article': 'TEST-002', 
                'name': 'Test Product 2',
                'stock': 20
            }
        ]
        mock_client_instance.get_turnover_report.return_value = []
        mock_client_instance.get_product_groups.return_value = []
        
        sync_service = SyncService()
        
        # Выполняем синхронизацию
        sync_log = sync_service.sync_products(
            warehouse_id='test-warehouse',
            excluded_groups=[],
            sync_type='manual',
            sync_images=False
        )
        
        # Проверяем, что sync_log был обновлен
        sync_log.refresh_from_db()
        
        # Проверяем корректные финальные значения
        self.assertEqual(sync_log.total_products, 2)
        self.assertEqual(sync_log.synced_products, 2)
        self.assertEqual(sync_log.status, 'success')
        self.assertEqual(sync_log.current_article, '')  # Должен быть очищен в конце
        
    def test_sync_log_progress_fields_not_null(self):
        """
        Тест: Поля прогресса в SyncLog не должны быть null
        """
        sync_log = SyncLog.objects.create(
            sync_type='manual',
            warehouse_id='test-warehouse',
            warehouse_name='Test Warehouse'
        )
        
        # Проверяем дефолтные значения
        self.assertEqual(sync_log.total_products, 0)
        self.assertEqual(sync_log.synced_products, 0)
        self.assertIsNotNone(sync_log.total_products)
        self.assertIsNotNone(sync_log.synced_products)
        
    def test_sync_log_current_article_updates(self):
        """
        Тест: Поле current_article обновляется корректно
        """
        sync_log = SyncLog.objects.create(
            sync_type='manual',
            warehouse_id='test-warehouse',
            warehouse_name='Test Warehouse'
        )
        
        # Симулируем обновление артикула
        sync_log.current_article = 'TEST-CURRENT-123'
        sync_log.save()
        
        sync_log.refresh_from_db()
        self.assertEqual(sync_log.current_article, 'TEST-CURRENT-123')


class FrontendProgressDisplayTests(TestCase):
    """
    Тесты для проверки отображения прогресса на frontend
    """
    
    def test_progress_calculation_logic(self):
        """
        Тест: Логика расчета прогресса корректна для frontend
        """
        # Тестируем различные сценарии прогресса
        test_cases = [
            {'total': 100, 'synced': 25, 'expected_percent': 25},
            {'total': 200, 'synced': 50, 'expected_percent': 25},
            {'total': 0, 'synced': 0, 'expected_percent': 0},
            {'total': 1, 'synced': 1, 'expected_percent': 100},
        ]
        
        for case in test_cases:
            with self.subTest(case=case):
                # Симулируем логику из frontend компонента
                total = case['total']
                synced = case['synced']
                
                if total > 0:
                    progress_percent = (synced / total) * 100
                else:
                    progress_percent = 0
                
                self.assertEqual(round(progress_percent), case['expected_percent'])