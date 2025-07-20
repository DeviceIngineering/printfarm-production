#!/usr/bin/env python
"""
Test updated production calculation logic
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.products.models import Product
from decimal import Decimal

def test_new_logic():
    print("=== Testing Updated Production Calculation Logic ===\n")
    
    # Test with theoretical cases
    test_cases = [
        {'sales': 2, 'stock': 3, 'type': 'old', 'name': 'Low sales (≤3) + low stock (<5)'},
        {'sales': 5, 'stock': 4, 'type': 'old', 'name': 'Medium sales (3<x<10) + low stock (≤6)'},
        {'sales': 15, 'stock': 8, 'type': 'old', 'name': 'High sales (≥10) existing logic'},
        {'sales': 1, 'stock': 6, 'type': 'critical', 'name': 'Critical: low sales + higher stock'},
    ]
    
    for i, case in enumerate(test_cases, 1):
        p = Product()
        p.sales_last_2_months = Decimal(str(case['sales']))
        p.current_stock = Decimal(str(case['stock']))
        p.product_type = case['type']
        p.average_daily_consumption = Decimal(str(case['sales'])) / Decimal('60')
        
        production_need = p.calculate_production_need()
        
        print(f'{i}. {case["name"]}:')
        print(f'   Sales: {case["sales"]}, Stock: {case["stock"]}, Type: {case["type"]}')
        print(f'   Production needed: {production_need}')
        print()
    
    # Test with real Подиумы products
    print("=== Testing with Real Подиумы Products ===\n")
    
    podiums_products = Product.objects.filter(product_group_name__icontains='Подиум').order_by('article')[:10]
    
    print(f'Found {podiums_products.count()} Подиумы products. Showing first 10:\n')
    
    for product in podiums_products:
        # Store old value
        old_production = product.production_needed
        
        # Force recalculation with new logic
        product.update_calculated_fields()
        new_production = product.production_needed
        
        print(f'Article: {product.article}')
        print(f'  Sales (2 months): {product.sales_last_2_months}')
        print(f'  Current stock: {product.current_stock}')
        print(f'  Type: {product.product_type}')
        print(f'  Production needed: {new_production}')
        if old_production != new_production:
            print(f'  ⚠️  Changed from {old_production} to {new_production}')
        print()

if __name__ == '__main__':
    test_new_logic()