#!/usr/bin/env python3
"""
Test updated calculation logic for product data.
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
django.setup()

from apps.products.models import Product
from apps.sync.services import SyncService
from decimal import Decimal

def test_classification_logic():
    """Test the updated product classification logic."""
    print("🧪 Testing product classification logic...")
    
    # Test cases: (stock, sales, expected_type)
    test_cases = [
        (3, 10, 'critical'),  # stock < 5 and sales > 0
        (3, 0, 'new'),        # stock < 5 and sales = 0
        (4, 3, 'critical'),   # stock < 5 and sales > 0 (critical takes priority)
        (6, 0, 'new'),        # sales = 0
        (10, 20, 'old'),      # normal case
        (8, 4, 'old'),        # sales < 5 but stock >= 5, so old
        (6, 4, 'old'),        # sales < 5 but stock >= 5, so old
    ]
    
    for i, (stock, sales, expected) in enumerate(test_cases):
        # Create temporary product for testing
        product = Product(
            moysklad_id=f'test-{i}',
            article=f'TEST-{i}',
            name=f'Test Product {i}',
            current_stock=Decimal(str(stock)),
            sales_last_2_months=Decimal(str(sales))
        )
        
        result = product.classify_product_type()
        status = "✅" if result == expected else "❌"
        print(f"  {status} Stock={stock}, Sales={sales} -> {result} (expected: {expected})")

def test_calculation_workflow():
    """Test the complete calculation workflow."""
    print("\n🧪 Testing complete calculation workflow...")
    
    # Create test product
    product = Product.objects.create(
        moysklad_id='test-calc',
        article='TEST-CALC',
        name='Test Calculation Product',
        current_stock=Decimal('8'),
        sales_last_2_months=Decimal('12'),
    )
    
    print(f"Test product created: {product.article}")
    print(f"  Current stock: {product.current_stock}")
    print(f"  Sales (2 months): {product.sales_last_2_months}")
    print(f"  Avg daily consumption: {product.average_daily_consumption}")
    print(f"  Days of stock: {product.days_of_stock}")
    print(f"  Product type: {product.product_type}")
    print(f"  Production needed: {product.production_needed}")
    print(f"  Production priority: {product.production_priority}")
    
    # Clean up
    product.delete()

def test_turnover_mapping():
    """Test article-based turnover mapping."""
    print("\n🧪 Testing turnover mapping logic...")
    
    # Sample turnover data structure (like from МойСклад)
    sample_turnover = [
        {
            'assortment': {
                'article': '375-42108',
                'name': 'Test Product 1'
            },
            'outcome': {
                'quantity': 15.0,
                'sum': 95000.0
            }
        },
        {
            'assortment': {
                'article': '376-41401', 
                'name': 'Test Product 2'
            },
            'outcome': {
                'quantity': 8.0,
                'sum': 48000.0
            }
        }
    ]
    
    # Build lookup dict like in updated sync service
    turnover_dict = {}
    for item in sample_turnover:
        assortment = item.get('assortment', {})
        article = assortment.get('article', '')
        if article:
            turnover_dict[article] = item
    
    print(f"Built turnover lookup for {len(turnover_dict)} products:")
    for article, data in turnover_dict.items():
        outcome_data = data.get('outcome', {})
        sales_qty = outcome_data.get('quantity', 0) if isinstance(outcome_data, dict) else outcome_data
        print(f"  {article}: sales = {sales_qty}")
    
    # Test matching with existing products
    existing_articles = list(Product.objects.values_list('article', flat=True)[:5])
    print(f"\nMatching with existing products:")
    for article in existing_articles:
        if article in turnover_dict:
            print(f"  ✅ {article} - found in turnover data")
        else:
            print(f"  ❌ {article} - not found in turnover data")

if __name__ == "__main__":
    print("🔬 Testing Updated Product Calculation Logic\n")
    
    test_classification_logic()
    test_calculation_workflow()
    test_turnover_mapping()
    
    print("\n✨ Testing completed!")
    print("\nNext step: Run actual sync to test with real data")