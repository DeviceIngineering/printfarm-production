"""
Django management command to test products API endpoints.
"""
from django.core.management.base import BaseCommand
from django.test import Client
from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token
from apps.products.models import Product
import json


class Command(BaseCommand):
    help = 'Test products API endpoints'

    def handle(self, *args, **options):
        self.stdout.write('Testing products API...')
        
        # Check products in database
        product_count = Product.objects.count()
        self.stdout.write(f'Products in database: {product_count}')
        
        if product_count > 0:
            # Show first 5 products
            products = Product.objects.order_by('-created_at')[:5]
            self.stdout.write('Recent products:')
            for product in products:
                self.stdout.write(f'  {product.article}: {product.name[:50]} (stock: {product.current_stock})')
        
        # Create test user and token if needed
        user, created = User.objects.get_or_create(
            username='testuser',
            defaults={'email': 'test@example.com'}
        )
        if created:
            user.set_password('testpass')
            user.save()
        
        token, created = Token.objects.get_or_create(user=user)
        self.stdout.write(f'Test token: {token.key}')
        
        # Test API endpoints
        client = Client()
        
        # Test products list endpoint
        self.stdout.write('\nTesting /api/v1/products/ endpoint...')
        response = client.get(
            '/api/v1/products/',
            HTTP_AUTHORIZATION=f'Token {token.key}'
        )
        self.stdout.write(f'Status: {response.status_code}')
        
        if response.status_code == 200:
            data = response.json()
            if 'results' in data:
                self.stdout.write(f'Products returned: {len(data["results"])}')
                self.stdout.write(f'Total count: {data.get("count", 0)}')
            else:
                self.stdout.write(f'Products returned: {len(data) if isinstance(data, list) else "Not a list"}')
        else:
            self.stdout.write(f'Error response: {response.content.decode()}')
        
        # Test stats endpoint
        self.stdout.write('\nTesting /api/v1/products/stats/ endpoint...')
        response = client.get(
            '/api/v1/products/stats/',
            HTTP_AUTHORIZATION=f'Token {token.key}'
        )
        self.stdout.write(f'Status: {response.status_code}')
        
        if response.status_code == 200:
            data = response.json()
            self.stdout.write(f'Stats: {json.dumps(data, indent=2)}')
        else:
            self.stdout.write(f'Error response: {response.content.decode()}')
            
        self.stdout.write(self.style.SUCCESS('API test completed!'))