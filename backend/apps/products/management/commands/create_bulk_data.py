"""
Management command to create bulk test data for performance testing.
"""
import random
from decimal import Decimal
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db import transaction
from apps.products.models import Product

class Command(BaseCommand):
    help = 'Create bulk test data for performance testing'

    def add_arguments(self, parser):
        parser.add_argument(
            '--count',
            type=int,
            default=10000,
            help='Number of products to create'
        )
        parser.add_argument(
            '--batch-size',
            type=int,
            default=1000,
            help='Batch size for bulk creation'
        )

    def handle(self, *args, **options):
        count = options['count']
        batch_size = options['batch_size']
        
        self.stdout.write(f'Creating {count} products in batches of {batch_size}...')
        
        # Clear existing products
        Product.objects.all().delete()
        
        # Product groups
        groups = [
            ('group-1', 'Канцелярские товары'),
            ('group-2', 'Офисная техника'),
            ('group-3', 'Расходные материалы'),
            ('group-4', 'Мебель'),
            ('group-5', 'Бытовая химия'),
            ('group-6', 'Электроника'),
            ('group-7', 'Инструменты'),
            ('group-8', 'Упаковочные материалы'),
            ('group-9', 'Сувенирная продукция'),
            ('group-10', 'Текстиль'),
        ]
        
        created = 0
        batch = []
        
        for i in range(count):
            group = random.choice(groups)
            
            # Generate varied data for testing algorithm
            if i % 4 == 0:  # Critical products (25%)
                current_stock = random.uniform(0, 4)
                sales = random.uniform(5, 50)
            elif i % 4 == 1:  # New products (25%)
                current_stock = random.uniform(0, 15)
                sales = random.uniform(0, 8)
            else:  # Old products (50%)
                current_stock = random.uniform(5, 200)
                sales = random.uniform(10, 300)
            
            # Calculate consumption
            consumption = sales / 60 if sales > 0 else 0
            
            product = Product(
                moysklad_id=f'bulk-product-{i+1:06d}',
                article=f'BULK-{i+1:06d}',
                name=f'Товар {i+1:06d} - {random.choice(["Стандарт", "Премиум", "Эконом", "Делюкс", "Профи", "Универсал"])}',
                description=f'Описание товара {i+1} для тестирования производительности',
                product_group_id=group[0],
                product_group_name=group[1],
                current_stock=Decimal(str(round(current_stock, 2))),
                sales_last_2_months=Decimal(str(round(sales, 2))),
                average_daily_consumption=Decimal(str(round(consumption, 4))),
                last_synced_at=timezone.now()
            )
            
            batch.append(product)
            
            if len(batch) >= batch_size:
                with transaction.atomic():
                    Product.objects.bulk_create(batch)
                created += len(batch)
                batch = []
                self.stdout.write(f'Created {created} products...')
        
        # Create remaining products
        if batch:
            with transaction.atomic():
                Product.objects.bulk_create(batch)
            created += len(batch)
        
        self.stdout.write(
            self.style.SUCCESS(f'Successfully created {created} products')
        )
        
        # Show statistics
        self.stdout.write('\nВычисляем статистику...')
        
        # Trigger calculation for all products
        products = Product.objects.all()
        batch_size = 1000
        updated = 0
        
        for i in range(0, products.count(), batch_size):
            batch_products = products[i:i+batch_size]
            for product in batch_products:
                product.update_calculated_fields()
            
            Product.objects.bulk_update(
                batch_products, 
                ['product_type', 'days_of_stock', 'production_needed', 'production_priority']
            )
            updated += len(batch_products)
            
            if updated % 5000 == 0:
                self.stdout.write(f'Updated {updated} products...')
        
        stats = {
            'total': Product.objects.count(),
            'new': Product.objects.filter(product_type='new').count(),
            'old': Product.objects.filter(product_type='old').count(),
            'critical': Product.objects.filter(product_type='critical').count(),
            'need_production': Product.objects.filter(production_needed__gt=0).count(),
        }
        
        self.stdout.write('\nФинальная статистика:')
        self.stdout.write(f'  Всего: {stats["total"]}')
        self.stdout.write(f'  Новые: {stats["new"]}')
        self.stdout.write(f'  Старые: {stats["old"]}')
        self.stdout.write(f'  Критические: {stats["critical"]}')
        self.stdout.write(f'  Требуют производства: {stats["need_production"]}')