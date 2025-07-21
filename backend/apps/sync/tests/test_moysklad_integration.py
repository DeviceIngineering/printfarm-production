"""
Tests for MoySklad integration.
"""
from unittest.mock import Mock, patch, MagicMock
from decimal import Decimal
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from apps.sync.moysklad_client import MoySkladClient
from apps.sync.services import SyncService
from apps.sync.models import SyncLog
from apps.products.models import Product


class MoySkladClientTestCase(TestCase):
    """Test cases for MoySkladClient."""
    
    def setUp(self):
        """Set up test client."""
        self.client = MoySkladClient()
    
    @patch('apps.sync.moysklad_client.requests.get')
    def test_get_warehouses_success(self, mock_get):
        """Test successful warehouse retrieval."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'rows': [
                {
                    'id': 'warehouse-1',
                    'name': 'Main Warehouse',
                    'meta': {'href': 'https://api.moysklad.ru/api/remap/1.2/entity/store/warehouse-1'}
                },
                {
                    'id': 'warehouse-2', 
                    'name': 'Secondary Warehouse',
                    'meta': {'href': 'https://api.moysklad.ru/api/remap/1.2/entity/store/warehouse-2'}
                }
            ]
        }
        mock_get.return_value = mock_response
        
        warehouses = self.client.get_warehouses()
        
        self.assertEqual(len(warehouses), 2)
        self.assertEqual(warehouses[0]['id'], 'warehouse-1')
        self.assertEqual(warehouses[0]['name'], 'Main Warehouse')
    
    @patch('apps.sync.moysklad_client.requests.get')
    def test_get_product_groups_success(self, mock_get):
        """Test successful product groups retrieval."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'rows': [
                {
                    'id': 'group-1',
                    'name': 'Electronics',
                    'pathName': 'Electronics'
                },
                {
                    'id': 'group-2',
                    'name': 'Office Supplies',
                    'pathName': 'Office Supplies'
                }
            ]
        }
        mock_get.return_value = mock_response
        
        groups = self.client.get_product_groups()
        
        self.assertEqual(len(groups), 2)
        self.assertEqual(groups[0]['id'], 'group-1')
        self.assertEqual(groups[0]['name'], 'Electronics')
    
    @patch('apps.sync.moysklad_client.requests.get')
    def test_api_error_handling(self, mock_get):
        """Test API error handling."""
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.raise_for_status.side_effect = Exception("Not Found")
        mock_get.return_value = mock_response
        
        with self.assertRaises(Exception):
            self.client.get_warehouses()
    
    @patch('apps.sync.moysklad_client.requests.get')
    def test_rate_limiting(self, mock_get):
        """Test rate limiting functionality."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'rows': []}
        mock_get.return_value = mock_response
        
        # Make multiple requests
        for _ in range(3):
            self.client.get_warehouses()
        
        # Should have made 3 requests
        self.assertEqual(mock_get.call_count, 3)


class SyncServiceTestCase(TestCase):
    """Test cases for SyncService."""
    
    def setUp(self):
        """Set up test data."""
        self.sync_service = SyncService()
    
    @patch.object(MoySkladClient, 'get_all_products_with_stock')
    def test_sync_products_success(self, mock_get_products):
        """Test successful product synchronization."""
        # Mock product data from MoySklad
        mock_products = [
            {
                'id': 'product-1',
                'article': 'ART-001',
                'name': 'Test Product 1',
                'description': 'Test description',
                'stock': Decimal('10'),
                'quantity': Decimal('5'),  # Sales quantity
                'folder': {
                    'meta': {
                        'href': 'https://api.moysklad.ru/api/remap/1.2/entity/productfolder/group-1'
                    },
                    'name': 'Test Group'
                }
            },
            {
                'id': 'product-2',
                'article': 'ART-002',
                'name': 'Test Product 2',
                'description': 'Another test',
                'stock': Decimal('0'),
                'quantity': Decimal('8'),
                'folder': None
            }
        ]
        mock_get_products.return_value = mock_products
        
        # Run synchronization
        sync_log = self.sync_service.sync_products(
            warehouse_id='test-warehouse',
            excluded_groups=[],
            sync_type='manual'
        )
        
        # Check sync log
        self.assertEqual(sync_log.status, 'success')
        self.assertEqual(sync_log.synced_products, 2)
        self.assertEqual(sync_log.total_products, 2)
        
        # Check created products
        self.assertEqual(Product.objects.count(), 2)
        
        product1 = Product.objects.get(article='ART-001')
        self.assertEqual(product1.name, 'Test Product 1')
        self.assertEqual(product1.current_stock, Decimal('10'))
        self.assertEqual(product1.sales_last_2_months, Decimal('5'))
        
        product2 = Product.objects.get(article='ART-002')
        self.assertEqual(product2.current_stock, Decimal('0'))
        self.assertEqual(product2.sales_last_2_months, Decimal('8'))
    
    @patch.object(MoySkladClient, 'get_all_products_with_stock')
    def test_sync_products_with_excluded_groups(self, mock_get_products):
        """Test product sync with excluded groups."""
        mock_products = [
            {
                'id': 'product-1',
                'article': 'ART-001',
                'name': 'Included Product',
                'stock': Decimal('5'),
                'quantity': Decimal('2'),
                'folder': {
                    'meta': {
                        'href': 'https://api.moysklad.ru/api/remap/1.2/entity/productfolder/group-included'
                    },
                    'name': 'Included Group'
                }
            },
            {
                'id': 'product-2', 
                'article': 'ART-002',
                'name': 'Excluded Product',
                'stock': Decimal('3'),
                'quantity': Decimal('1'),
                'folder': {
                    'meta': {
                        'href': 'https://api.moysklad.ru/api/remap/1.2/entity/productfolder/group-excluded'
                    },
                    'name': 'Excluded Group'
                }
            }
        ]
        mock_get_products.return_value = mock_products
        
        # Run sync with excluded group
        sync_log = self.sync_service.sync_products(
            warehouse_id='test-warehouse',
            excluded_groups=['group-excluded'],
            sync_type='manual'
        )
        
        # Should only sync the included product
        self.assertEqual(Product.objects.count(), 1)
        self.assertTrue(Product.objects.filter(article='ART-001').exists())
        self.assertFalse(Product.objects.filter(article='ART-002').exists())
    
    @patch.object(MoySkladClient, 'get_all_products_with_stock')
    def test_sync_products_error_handling(self, mock_get_products):
        """Test error handling during sync."""
        mock_get_products.side_effect = Exception("API Error")
        
        sync_log = self.sync_service.sync_products(
            warehouse_id='test-warehouse',
            excluded_groups=[],
            sync_type='manual'
        )
        
        self.assertEqual(sync_log.status, 'failed')
        self.assertIn('API Error', sync_log.error_details)
    
    def test_update_existing_product(self):
        """Test updating existing product during sync."""
        # Create existing product
        existing_product = Product.objects.create(
            moysklad_id='product-1',
            article='ART-001',
            name='Old Name',
            current_stock=Decimal('5'),
            sales_last_2_months=Decimal('3')
        )
        
        # Mock updated data
        with patch.object(MoySkladClient, 'get_all_products_with_stock') as mock_get:
            mock_get.return_value = [
                {
                    'id': 'product-1',
                    'article': 'ART-001', 
                    'name': 'Updated Name',
                    'description': 'Updated description',
                    'stock': Decimal('15'),
                    'quantity': Decimal('8'),
                    'folder': None
                }
            ]
            
            self.sync_service.sync_products(
                warehouse_id='test-warehouse',
                excluded_groups=[],
                sync_type='manual'
            )
        
        # Check product was updated
        updated_product = Product.objects.get(moysklad_id='product-1')
        self.assertEqual(updated_product.name, 'Updated Name')
        self.assertEqual(updated_product.current_stock, Decimal('15'))
        self.assertEqual(updated_product.sales_last_2_months, Decimal('8'))


class SyncAPITestCase(TestCase):
    """Test cases for Sync API endpoints."""
    
    def setUp(self):
        """Set up test client."""
        self.api_client = APIClient()
    
    @patch.object(MoySkladClient, 'get_warehouses')
    def test_sync_warehouses_endpoint(self, mock_get_warehouses):
        """Test GET /api/v1/sync/warehouses/ endpoint."""
        mock_warehouses = [
            {'id': 'wh-1', 'name': 'Warehouse 1'},
            {'id': 'wh-2', 'name': 'Warehouse 2'}
        ]
        mock_get_warehouses.return_value = mock_warehouses
        
        url = reverse('sync:warehouses')
        response = self.api_client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
        self.assertEqual(response.data[0]['name'], 'Warehouse 1')
    
    @patch.object(MoySkladClient, 'get_product_groups')
    def test_sync_product_groups_endpoint(self, mock_get_groups):
        """Test GET /api/v1/sync/product-groups/ endpoint."""
        mock_groups = [
            {'id': 'gr-1', 'name': 'Group 1', 'pathName': 'Group 1'},
            {'id': 'gr-2', 'name': 'Group 2', 'pathName': 'Group 2'}
        ]
        mock_get_groups.return_value = mock_groups
        
        url = reverse('sync:product-groups')
        response = self.api_client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
        self.assertEqual(response.data[0]['name'], 'Group 1')
    
    def test_sync_status_endpoint(self):
        """Test GET /api/v1/sync/status/ endpoint."""
        url = reverse('sync:status')
        response = self.api_client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('is_syncing', response.data)
    
    @patch.object(SyncService, 'sync_products')
    def test_start_sync_endpoint(self, mock_sync):
        """Test POST /api/v1/sync/start/ endpoint."""
        # Mock successful sync
        mock_sync_log = Mock()
        mock_sync_log.id = 1
        mock_sync_log.status = 'success'
        mock_sync_log.synced_products = 10
        mock_sync_log.total_products = 10
        mock_sync_log.failed_products = 0
        mock_sync.return_value = mock_sync_log
        
        url = reverse('sync:start')
        data = {
            'warehouse_id': 'test-warehouse',
            'excluded_groups': [],
            'sync_images': True
        }
        response = self.api_client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('sync_id', response.data)
        self.assertEqual(response.data['status'], 'success')
    
    def test_start_sync_missing_warehouse(self):
        """Test start sync without warehouse_id."""
        url = reverse('sync:start')
        data = {}
        response = self.api_client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
    
    def test_sync_history_endpoint(self):
        """Test GET /api/v1/sync/history/ endpoint."""
        # Create test sync log
        SyncLog.objects.create(
            sync_type='manual',
            status='success',
            warehouse_id='test-warehouse',
            warehouse_name='Test Warehouse',
            total_products=5,
            synced_products=5
        )
        
        url = reverse('sync:history')
        response = self.api_client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['sync_type'], 'manual')
        self.assertEqual(response.data[0]['status'], 'success')