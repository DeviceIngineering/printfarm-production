#!/usr/bin/env python
"""
Recalculate all products with updated production logic
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.products.models import Product

def main():
    print("=== Updating All Products with New Production Logic ===\n")
    
    # Get all products count
    total_products = Product.objects.count()
    print(f'Found {total_products} total products in database')
    
    # Update all products with new logic
    print('Updating all products with new production calculation logic...')
    
    updated_count = 0
    products_with_changes = []
    
    for product in Product.objects.all():
        # Store old values
        old_production = product.production_needed
        old_priority = product.production_priority
        
        # Update with new logic
        product.update_calculated_fields()
        product.save()
        
        # Check for changes
        if old_production != product.production_needed or old_priority != product.production_priority:
            products_with_changes.append({
                'article': product.article,
                'old_production': old_production,
                'new_production': product.production_needed,
                'old_priority': old_priority,
                'new_priority': product.production_priority,
                'sales': product.sales_last_2_months,
                'stock': product.current_stock,
                'type': product.product_type
            })
        
        updated_count += 1
        if updated_count % 100 == 0:
            print(f'  Updated {updated_count}/{total_products} products...')
    
    print(f'\n✅ Successfully updated {updated_count} products')
    print(f'📊 {len(products_with_changes)} products had changes in production calculations')
    
    if products_with_changes:
        print('\nProducts with changes:')
        for item in products_with_changes[:10]:  # Show first 10
            print(f'  {item["article"]}: Production {item["old_production"]} → {item["new_production"]} (Sales: {item["sales"]}, Stock: {item["stock"]}, Type: {item["type"]})')
        
        if len(products_with_changes) > 10:
            print(f'  ... and {len(products_with_changes) - 10} more products')
    
    # Show summary of products needing production
    products_needing_production = Product.objects.filter(production_needed__gt=0).count()
    print(f'\n📈 Total products needing production: {products_needing_production}')

if __name__ == '__main__':
    main()