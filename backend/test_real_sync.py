#!/usr/bin/env python3
"""
Test real synchronization with updated logic.
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

def test_real_sync():
    """Test real sync with small dataset."""
    print("🔄 Testing real sync with updated logic...")
    
    # Clear existing products to see fresh results
    initial_count = Product.objects.count()
    print(f"Initial products count: {initial_count}")
    
    # Initialize sync service
    sync_service = SyncService()
    warehouse_id = '241ed919-a631-11ee-0a80-07a9000bb947'
    
    # Test with group exclusion to limit dataset
    excluded_groups = [
        # Keep only one group for testing
        '821002ca-9221-11ef-0a80-16900019d6e0'  # Geely Monjaro group (has data in turnover)
    ]
    
    try:
        print(f"Starting sync with excluded groups: {len(excluded_groups)}")
        sync_log = sync_service.sync_products(
            warehouse_id=warehouse_id,
            excluded_groups=excluded_groups,
            sync_type='manual',
            sync_images=False  # Skip images for speed
        )
        
        print(f"✅ Sync completed!")
        print(f"  Status: {sync_log.status}")
        print(f"  Total: {sync_log.total_products}")
        print(f"  Synced: {sync_log.synced_products}")
        print(f"  Failed: {sync_log.failed_products}")
        
        # Analyze results
        print(f"\n📊 Results Analysis:")
        total_products = Product.objects.count()
        print(f"Total products after sync: {total_products}")
        
        # Check data filling
        with_sales = Product.objects.filter(sales_last_2_months__gt=0).count()
        with_consumption = Product.objects.filter(average_daily_consumption__gt=0).count()
        with_days_stock = Product.objects.filter(days_of_stock__isnull=False).count()
        with_production_needed = Product.objects.filter(production_needed__gt=0).count()
        
        print(f"\nData filling status:")
        print(f"  Products with sales > 0: {with_sales}/{total_products} ({with_sales/total_products*100:.1f}%)")
        print(f"  Products with consumption > 0: {with_consumption}/{total_products} ({with_consumption/total_products*100:.1f}%)")
        print(f"  Products with days_of_stock: {with_days_stock}/{total_products} ({with_days_stock/total_products*100:.1f}%)")
        print(f"  Products needing production: {with_production_needed}/{total_products} ({with_production_needed/total_products*100:.1f}%)")
        
        # Type distribution
        print(f"\nProduct type distribution:")
        for product_type, _ in Product.PRODUCT_TYPE_CHOICES:
            count = Product.objects.filter(product_type=product_type).count()
            print(f"  {product_type}: {count}")
        
        # Show examples with sales data
        print(f"\n📋 Examples with sales data:")
        products_with_sales = Product.objects.filter(sales_last_2_months__gt=0)[:5]
        for product in products_with_sales:
            print(f"  {product.article}: stock={product.current_stock}, sales={product.sales_last_2_months}, "
                  f"daily={product.average_daily_consumption}, days={product.days_of_stock}, "
                  f"type={product.product_type}, priority={product.production_priority}")
        
        # Show examples without sales data
        print(f"\n📋 Examples without sales data:")
        products_no_sales = Product.objects.filter(sales_last_2_months=0)[:3]
        for product in products_no_sales:
            print(f"  {product.article}: stock={product.current_stock}, sales={product.sales_last_2_months}, "
                  f"type={product.product_type}, needed={product.production_needed}")
        
    except Exception as e:
        print(f"❌ Sync failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_real_sync()