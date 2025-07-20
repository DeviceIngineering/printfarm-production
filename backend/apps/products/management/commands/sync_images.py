"""
Django management command to sync product images from МойСклад.
"""
from django.core.management.base import BaseCommand
from apps.products.models import Product
from apps.sync.services import SyncService


class Command(BaseCommand):
    help = 'Sync product images from МойСклад'

    def add_arguments(self, parser):
        parser.add_argument(
            '--limit',
            type=int,
            help='Limit number of products to sync images for',
            default=10
        )
        parser.add_argument(
            '--product-id',
            type=int,
            help='Sync images for specific product ID'
        )

    def handle(self, *args, **options):
        sync_service = SyncService()
        
        if options['product_id']:
            try:
                product = Product.objects.get(id=options['product_id'])
                self.stdout.write(f'Syncing images for product: {product.article}')
                
                synced_count = sync_service.sync_product_images(product)
                self.stdout.write(self.style.SUCCESS(
                    f'Synced {synced_count} images for product {product.article}'
                ))
            except Product.DoesNotExist:
                self.stdout.write(self.style.ERROR(f'Product with ID {options["product_id"]} not found'))
            return
        
        # Sync images for multiple products
        limit = options['limit']
        self.stdout.write(f'Syncing images for up to {limit} products...')
        
        # Get products without images that were synced from МойСклад
        products_without_images = Product.objects.filter(
            images__isnull=True,
            last_synced_at__isnull=False
        ).distinct()[:limit]
        
        total_synced = 0
        for i, product in enumerate(products_without_images, 1):
            self.stdout.write(f'Processing {i}/{len(products_without_images)}: {product.article}')
            
            try:
                synced_count = sync_service.sync_product_images(product)
                total_synced += synced_count
                
                if synced_count > 0:
                    self.stdout.write(f'  ✓ Synced {synced_count} images')
                else:
                    self.stdout.write(f'  - No images found')
                    
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'  ✗ Error: {str(e)}'))
        
        self.stdout.write(self.style.SUCCESS(
            f'Completed! Total images synced: {total_synced} for {len(products_without_images)} products'
        ))