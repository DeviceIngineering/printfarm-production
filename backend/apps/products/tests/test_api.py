"""
Tests for Products API endpoints.
"""
from decimal import Decimal
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from apps.products.models import Product
from apps.sync.models import ProductionList


class ProductsAPITestCase(TestCase):
    """Test cases for Products API endpoints."""
    
    def setUp(self):
        """Set up test data."""
        self.client = APIClient()
        
        # Create test products
        self.product1 = Product.objects.create(
            moysklad_id='test-001',
            article='TEST-001',
            name='Test Product 1',
            current_stock=Decimal('5'),
            sales_last_2_months=Decimal('10')
        )
        
        self.product2 = Product.objects.create(
            moysklad_id='test-002',
            article='TEST-002', 
            name='Test Product 2',
            current_stock=Decimal('0'),
            sales_last_2_months=Decimal('5')
        )
    
    def test_products_list_endpoint(self):
        """Test GET /api/v1/products/ endpoint."""
        url = reverse('product-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)
        self.assertEqual(len(response.data['results']), 2)
        
        # Check product data structure
        product_data = response.data['results'][0]
        expected_fields = [
            'id', 'article', 'name', 'current_stock', 'sales_last_2_months',
            'product_type', 'production_needed', 'production_priority', 'days_of_stock'
        ]
        for field in expected_fields:
            self.assertIn(field, product_data)
    
    def test_products_list_search(self):
        """Test product search functionality."""
        url = reverse('product-list')
        
        # Search by article
        response = self.client.get(url, {'search': 'TEST-001'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['article'], 'TEST-001')
        
        # Search by name
        response = self.client.get(url, {'search': 'Test Product 2'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['name'], 'Test Product 2')
    
    def test_products_list_filtering(self):
        """Test product filtering."""
        url = reverse('product-list')
        
        # Filter by product type
        critical_products = Product.objects.filter(product_type='critical')
        if critical_products.exists():
            response = self.client.get(url, {'product_type': 'critical'})
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            for product in response.data['results']:
                self.assertEqual(product['product_type'], 'critical')
    
    def test_product_detail_endpoint(self):
        """Test GET /api/v1/products/{id}/ endpoint."""
        url = reverse('product-detail', kwargs={'pk': self.product1.pk})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['article'], 'TEST-001')
        self.assertEqual(response.data['name'], 'Test Product 1')
    
    def test_product_stats_endpoint(self):
        """Test GET /api/v1/products/stats/ endpoint."""
        url = reverse('product-stats')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        expected_fields = [
            'total_products', 'new_products', 'old_products', 
            'critical_products', 'production_needed_items', 'total_production_units'
        ]
        for field in expected_fields:
            self.assertIn(field, response.data)
        
        self.assertEqual(response.data['total_products'], 2)
    
    def test_recalculate_production_endpoint(self):
        """Test POST /api/v1/products/recalculate/ endpoint."""
        url = reverse('recalculate-production')
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('updated_products', response.data)
        self.assertIn('total_products', response.data)
    
    def test_calculate_production_list_endpoint(self):
        """Test POST /api/v1/products/calculate-production-list/ endpoint."""
        url = reverse('calculate-production-list')
        
        data = {
            'min_priority': 20,
            'apply_coefficients': True
        }
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('production_list_id', response.data)
        self.assertIn('total_items', response.data)
        
        # Verify production list was created
        production_list_id = response.data['production_list_id']
        self.assertTrue(ProductionList.objects.filter(id=production_list_id).exists())
    
    def test_get_production_list_endpoint(self):
        """Test GET /api/v1/products/production-list/ endpoint."""
        # First create a production list
        from apps.products.services import ProductionService
        service = ProductionService()
        production_list = service.calculate_production_list()
        
        url = reverse('get-production-list-by-id', kwargs={'list_id': production_list.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('id', response.data)
        self.assertIn('items', response.data)
        self.assertIn('total_items', response.data)
    
    def test_production_stats_endpoint(self):
        """Test GET /api/v1/products/production-stats/ endpoint."""
        url = reverse('production-stats')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # The exact structure depends on ProductionService.get_production_stats()
        self.assertIsInstance(response.data, dict)


class ProductModelTestCase(TestCase):
    """Test cases for Product model methods."""
    
    def test_product_string_representation(self):
        """Test Product __str__ method."""
        product = Product.objects.create(
            moysklad_id='test-str-001',
            article='STR-001',
            name='A very long product name that should be truncated in string representation',
            current_stock=Decimal('10'),
            sales_last_2_months=Decimal('5')
        )
        
        expected = 'STR-001 - A very long product name that should be truncated '
        self.assertEqual(str(product), expected)
    
    def test_update_calculated_fields_method(self):
        """Test that update_calculated_fields works correctly."""
        product = Product.objects.create(
            moysklad_id='test-calc-001',
            article='CALC-001', 
            name='Calculation Test Product',
            current_stock=Decimal('3'),
            sales_last_2_months=Decimal('12')
        )
        
        # Fields should be calculated automatically on save
        self.assertGreater(product.average_daily_consumption, Decimal('0'))
        self.assertIn(product.product_type, ['new', 'old', 'critical'])
        self.assertGreaterEqual(product.production_priority, 0)
        
        # Test manual recalculation
        old_priority = product.production_priority
        product.sales_last_2_months = Decimal('0')  # Change sales to trigger recalculation
        product.update_calculated_fields()
        
        self.assertEqual(product.product_type, 'new')  # Should become new product
        # Priority might change based on new classification