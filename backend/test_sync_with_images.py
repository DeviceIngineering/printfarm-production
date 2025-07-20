#!/usr/bin/env python3
"""
Test script for sync with images functionality.
"""
import os
import sys
import django

# Setup Django
sys.path.append('/Users/dim11/Documents/myProjects/Factory_v2/backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()

from apps.sync.services import SyncService
from apps.products.models import Product

def test_sync_with_images():
    """Test sync with image integration."""
    print("🚀 Starting sync test with images...")
    
    # Get initial counts
    initial_products = Product.objects.count()
    initial_with_images = Product.objects.filter(images__isnull=False).distinct().count()
    
    print(f"📊 Initial state:")
    print(f"   Products: {initial_products}")
    print(f"   With images: {initial_with_images}")
    
    try:
        # Start sync with images enabled
        sync_service = SyncService()
        warehouse_id = '241ed919-a631-11ee-0a80-07a9000bb947'  # Default warehouse
        
        print(f"🔄 Starting sync from warehouse {warehouse_id}...")
        
        sync_log = sync_service.sync_products(
            warehouse_id=warehouse_id,
            excluded_groups=[],
            sync_type='manual',
            sync_images=True
        )
        
        print(f"✅ Sync completed!")
        print(f"   Status: {sync_log.status}")
        print(f"   Products synced: {sync_log.synced_products}/{sync_log.total_products}")
        print(f"   Failed: {sync_log.failed_products}")
        
        # Get final counts
        final_products = Product.objects.count()
        final_with_images = Product.objects.filter(images__isnull=False).distinct().count()
        
        print(f"📊 Final state:")
        print(f"   Products: {final_products} (+{final_products - initial_products})")
        print(f"   With images: {final_with_images} (+{final_with_images - initial_with_images})")
        
        # Show some products with images
        products_with_images = Product.objects.filter(images__isnull=False).distinct()[:5]
        print(f"🖼️  Sample products with images:")
        for product in products_with_images:
            print(f"   - {product.article}: {product.name} ({product.images.count()} images)")
        
    except Exception as e:
        print(f"❌ Sync failed: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    test_sync_with_images()