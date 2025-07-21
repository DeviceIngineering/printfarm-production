"""
Test factories for Product models.
"""
import factory
from decimal import Decimal
from apps.products.models import Product, ProductImage


class ProductFactory(factory.django.DjangoModelFactory):
    """Factory for creating test Product instances."""
    
    class Meta:
        model = Product
    
    moysklad_id = factory.Sequence(lambda n: f'test-product-{n}')
    article = factory.Sequence(lambda n: f'ART-{n:03d}')
    name = factory.Faker('sentence', nb_words=3)
    description = factory.Faker('text', max_nb_chars=200)
    
    product_group_id = factory.Faker('uuid4')
    product_group_name = factory.Faker('word')
    
    current_stock = factory.LazyFunction(lambda: Decimal(str(factory.Faker('random_int', min=0, max=50).generate())))
    sales_last_2_months = factory.LazyFunction(lambda: Decimal(str(factory.Faker('random_int', min=0, max=30).generate())))
    
    @classmethod
    def create_critical_product(cls, **kwargs):
        """Create a critical product (low stock + has sales)."""
        defaults = {
            'current_stock': Decimal('2'),
            'sales_last_2_months': Decimal('10')
        }
        defaults.update(kwargs)
        return cls.create(**defaults)
    
    @classmethod  
    def create_new_product(cls, **kwargs):
        """Create a new product (no sales)."""
        defaults = {
            'current_stock': Decimal('3'),
            'sales_last_2_months': Decimal('0')
        }
        defaults.update(kwargs)
        return cls.create(**defaults)
    
    @classmethod
    def create_old_product_low_sales(cls, **kwargs):
        """Create old product with low sales."""
        defaults = {
            'current_stock': Decimal('8'),
            'sales_last_2_months': Decimal('2')
        }
        defaults.update(kwargs)
        return cls.create(**defaults)
    
    @classmethod
    def create_old_product_medium_sales(cls, **kwargs):
        """Create old product with medium sales."""
        defaults = {
            'current_stock': Decimal('5'),
            'sales_last_2_months': Decimal('7')
        }
        defaults.update(kwargs)
        return cls.create(**defaults)
    
    @classmethod
    def create_old_product_high_sales(cls, **kwargs):
        """Create old product with high sales."""
        defaults = {
            'current_stock': Decimal('3'),
            'sales_last_2_months': Decimal('25')
        }
        defaults.update(kwargs)
        return cls.create(**defaults)


class ProductImageFactory(factory.django.DjangoModelFactory):
    """Factory for creating test ProductImage instances."""
    
    class Meta:
        model = ProductImage
    
    product = factory.SubFactory(ProductFactory)
    moysklad_url = factory.Faker('url')
    is_main = False