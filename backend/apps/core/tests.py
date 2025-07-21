"""
Core application tests.
"""
from django.test import TestCase
from django.urls import reverse, resolve
from rest_framework.test import APIClient
from rest_framework import status


class URLsTestCase(TestCase):
    """Test URL routing and basic endpoint availability."""
    
    def setUp(self):
        """Set up test client."""
        self.client = APIClient()
    
    def test_products_urls_resolve(self):
        """Test that product URLs resolve correctly."""
        urls_to_test = [
            ('products:product-list', {}),
            ('products:product-stats', {}),
            ('products:production-stats', {}),
            ('products:recalculate-production', {}),
            ('products:calculate-production-list', {}),
        ]
        
        for url_name, kwargs in urls_to_test:
            with self.subTest(url_name=url_name):
                url = reverse(url_name, kwargs=kwargs)
                self.assertIsNotNone(url)
                
                # Test that URL resolves to a view
                resolver = resolve(url)
                self.assertIsNotNone(resolver.func)
    
    def test_sync_urls_resolve(self):
        """Test that sync URLs resolve correctly."""
        urls_to_test = [
            ('sync:warehouses', {}),
            ('sync:product-groups', {}),
            ('sync:status', {}),
            ('sync:start', {}),
            ('sync:history', {}),
        ]
        
        for url_name, kwargs in urls_to_test:
            with self.subTest(url_name=url_name):
                url = reverse(url_name, kwargs=kwargs)
                self.assertIsNotNone(url)
                
                resolver = resolve(url)
                self.assertIsNotNone(resolver.func)
    
    def test_api_endpoints_respond(self):
        """Test that API endpoints respond (even if empty)."""
        get_endpoints = [
            '/api/v1/products/',
            '/api/v1/products/stats/',
            '/api/v1/products/production-stats/',
            '/api/v1/sync/warehouses/',
            '/api/v1/sync/product-groups/',
            '/api/v1/sync/status/',
            '/api/v1/sync/history/',
        ]
        
        for endpoint in get_endpoints:
            with self.subTest(endpoint=endpoint):
                response = self.client.get(endpoint)
                # Should not return 404 or 500
                self.assertNotEqual(response.status_code, status.HTTP_404_NOT_FOUND)
                self.assertLess(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def test_post_endpoints_validation(self):
        """Test that POST endpoints handle validation properly."""
        post_endpoints = [
            ('/api/v1/products/recalculate/', {}),
            ('/api/v1/products/calculate-production-list/', {'min_priority': 20}),
            ('/api/v1/sync/start/', {'warehouse_id': 'test'}),
        ]
        
        for endpoint, data in post_endpoints:
            with self.subTest(endpoint=endpoint):
                response = self.client.post(endpoint, data, format='json')
                # Should not return 404 or 500, might return 400 for validation
                self.assertNotEqual(response.status_code, status.HTTP_404_NOT_FOUND)
                self.assertLess(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
