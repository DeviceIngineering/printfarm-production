"""
Management command to create test data for demonstration.
"""
import random
from decimal import Decimal
from django.core.management.base import BaseCommand
from django.utils import timezone
from apps.products.models import Product

class Command(BaseCommand):
    help = 'Create test data for demonstration'

    def add_arguments(self, parser):
        parser.add_argument(
            '--count',
            type=int,
            default=100,
            help='Number of products to create'
        )

    def handle(self, *args, **options):
        count = options['count']
        
        self.stdout.write(f'Creating {count} test products...')
        
        # Clear existing products
        Product.objects.all().delete()
        
        # Product groups
        groups = [
            ('group-1', 'Канцелярские товары'),
            ('group-2', 'Офисная техника'),
            ('group-3', 'Расходные материалы'),
            ('group-4', 'Мебель'),
            ('group-5', 'Бытовая химия'),
        ]
        
        # Product types for varied testing
        product_types = ['new', 'old', 'critical']
        
        for i in range(count):
            group = random.choice(groups)
            
            # Generate varied data for testing algorithm
            if i % 3 == 0:  # Critical products
                current_stock = random.uniform(0, 4)
                sales = random.uniform(5, 50)
                product_type = 'critical'
            elif i % 3 == 1:  # New products
                current_stock = random.uniform(0, 15)
                sales = random.uniform(0, 8)
                product_type = 'new'
            else:  # Old products
                current_stock = random.uniform(5, 100)
                sales = random.uniform(10, 200)
                product_type = 'old'
            
            # Calculate consumption
            consumption = sales / 60 if sales > 0 else 0
            
            product = Product.objects.create(
                moysklad_id=f'test-product-{i+1:04d}',
                article=f'ART-{i+1:04d}',
                name=f'Тестовый товар {i+1:04d} - {random.choice(["Стандарт", "Премиум", "Эконом", "Делюкс"])}',
                description=f'Описание тестового товара {i+1}',
                product_group_id=group[0],
                product_group_name=group[1],
                current_stock=Decimal(str(round(current_stock, 2))),
                sales_last_2_months=Decimal(str(round(sales, 2))),
                average_daily_consumption=Decimal(str(round(consumption, 4))),
                last_synced_at=timezone.now()
            )
            
            if i % 50 == 0:
                self.stdout.write(f'Created {i+1} products...')
        
        self.stdout.write(
            self.style.SUCCESS(f'Successfully created {count} test products')
        )
        
        # Show statistics
        stats = {
            'total': Product.objects.count(),
            'new': Product.objects.filter(product_type='new').count(),
            'old': Product.objects.filter(product_type='old').count(),
            'critical': Product.objects.filter(product_type='critical').count(),
            'need_production': Product.objects.filter(production_needed__gt=0).count(),
        }
        
        self.stdout.write('\nСтатистика созданных товаров:')
        self.stdout.write(f'  Всего: {stats["total"]}')
        self.stdout.write(f'  Новые: {stats["new"]}')
        self.stdout.write(f'  Старые: {stats["old"]}')
        self.stdout.write(f'  Критические: {stats["critical"]}')
        self.stdout.write(f'  Требуют производства: {stats["need_production"]}')