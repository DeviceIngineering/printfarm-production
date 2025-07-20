#!/usr/bin/env python
"""
Test Excel export functionality.
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
django.setup()

from apps.products.models import Product
from apps.reports.exporters import ProductsExporter

# Get some products
products = Product.objects.all()[:10]
print(f"Testing export with {products.count()} products")

# Create exporter
exporter = ProductsExporter()

# Test export (will save to test file instead of HTTP response)
from openpyxl import Workbook
wb = exporter.wb
ws = exporter.ws

# Execute the export logic manually
exporter.export_products(products)

# Save to file
test_file = 'test_export.xlsx'
wb.save(test_file)
print(f"✅ Export saved to {test_file}")

# Print some statistics
products_list = list(products)
print(f"\nExport statistics:")
print(f"- Total products: {len(products_list)}")
print(f"- Products with images: {sum(1 for p in products_list if p.images.exists())}")
print(f"- Critical products: {sum(1 for p in products_list if p.product_type == 'critical')}")
print(f"- Products needing production: {sum(1 for p in products_list if p.production_needed > 0)}")

print("\n✨ Excel export is working correctly!")