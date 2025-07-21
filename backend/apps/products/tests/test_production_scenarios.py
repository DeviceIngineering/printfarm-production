"""
Tests for production calculation scenarios using factories.
"""
from decimal import Decimal
from django.test import TestCase
from .factories import ProductFactory
from apps.products.services import ProductionService


class ProductionScenariosTestCase(TestCase):
    """Test real-world production scenarios."""
    
    def setUp(self):
        """Set up test service."""
        self.production_service = ProductionService()
    
    def test_mixed_product_production_list(self):
        """Test production list calculation with mixed product types."""
        # Create various product types
        critical_products = [
            ProductFactory.create_critical_product(
                article=f'CRIT-{i:03d}',
                current_stock=Decimal('1'),
                sales_last_2_months=Decimal('8')
            ) for i in range(3)
        ]
        
        new_products = [
            ProductFactory.create_new_product(
                article=f'NEW-{i:03d}',
                current_stock=Decimal('2'),
                sales_last_2_months=Decimal('0')
            ) for i in range(5)
        ]
        
        old_low_sales = [
            ProductFactory.create_old_product_low_sales(
                article=f'OLD-LOW-{i:03d}',
                current_stock=Decimal('7'),
                sales_last_2_months=Decimal('3')
            ) for i in range(4)
        ]
        
        old_medium_sales = [
            ProductFactory.create_old_product_medium_sales(
                article=f'OLD-MED-{i:03d}',
                current_stock=Decimal('4'),
                sales_last_2_months=Decimal('8')
            ) for i in range(6)
        ]
        
        # Calculate production list
        production_list = self.production_service.calculate_production_list(
            min_priority=20,
            apply_coefficients=True
        )
        
        # Verify production list structure
        self.assertGreater(production_list.total_items, 0)
        self.assertGreater(production_list.total_units, Decimal('0'))
        
        # Check that critical products have highest priority
        items = production_list.items.all()
        if items.exists():
            # First items should have highest priority products
            first_item = items.first()
            self.assertGreaterEqual(first_item.product.production_priority, 60)
    
    def test_assortment_strategy_application(self):
        """Test that assortment strategy is applied when >= 30 products."""
        # Create 35 products needing production
        products = []
        for i in range(35):
            if i < 10:
                # High priority products
                product = ProductFactory.create_critical_product(
                    article=f'HIGH-{i:03d}',
                    current_stock=Decimal('1'),
                    sales_last_2_months=Decimal('15')
                )
            elif i < 20:
                # Medium priority products  
                product = ProductFactory.create_old_product_medium_sales(
                    article=f'MED-{i:03d}',
                    current_stock=Decimal('3'),
                    sales_last_2_months=Decimal('8')
                )
            else:
                # Lower priority products
                product = ProductFactory.create_new_product(
                    article=f'LOW-{i:03d}',
                    current_stock=Decimal('2'),
                    sales_last_2_months=Decimal('0')
                )
            products.append(product)
        
        # Calculate production list
        production_list = self.production_service.calculate_production_list(
            min_priority=20,
            apply_coefficients=True
        )
        
        # With >= 30 products, assortment strategy should apply coefficients
        # Higher priority items should get higher quantities
        items = production_list.items.order_by('priority')[:10]
        high_priority_quantities = [item.quantity for item in items]
        
        items = production_list.items.order_by('-priority')[:10]  
        low_priority_quantities = [item.quantity for item in items]
        
        # High priority items should generally have higher quantities
        if high_priority_quantities and low_priority_quantities:
            avg_high = sum(high_priority_quantities) / len(high_priority_quantities)
            avg_low = sum(low_priority_quantities) / len(low_priority_quantities) 
            self.assertGreaterEqual(avg_high, avg_low)
    
    def test_minimum_priority_filtering(self):
        """Test filtering products by minimum priority."""
        # Create products with different priorities
        high_priority = ProductFactory.create_critical_product(
            article='HIGH-001',
            current_stock=Decimal('1'),
            sales_last_2_months=Decimal('10')
        )
        
        medium_priority = ProductFactory.create_old_product_medium_sales(
            article='MED-001', 
            current_stock=Decimal('5'),
            sales_last_2_months=Decimal('6')
        )
        
        low_priority = ProductFactory.create_new_product(
            article='LOW-001',
            current_stock=Decimal('8'),
            sales_last_2_months=Decimal('0')
        )
        
        # Test with high minimum priority
        production_list = self.production_service.calculate_production_list(
            min_priority=80,
            apply_coefficients=False
        )
        
        # Should only include high priority products
        articles_in_list = [item.product.article for item in production_list.items.all()]
        
        if production_list.total_items > 0:
            # High priority products should be included
            high_priority_included = any(
                item.product.production_priority >= 80 
                for item in production_list.items.all()
            )
            self.assertTrue(high_priority_included)
    
    def test_zero_production_needed_exclusion(self):
        """Test that products with zero production need are excluded."""
        # Create products that don't need production
        sufficient_stock = ProductFactory.create_old_product_low_sales(
            article='SUFFICIENT-001',
            current_stock=Decimal('20'),  # High stock
            sales_last_2_months=Decimal('2')  # Low sales
        )
        
        # Create product that needs production
        needs_production = ProductFactory.create_critical_product(
            article='NEEDS-001',
            current_stock=Decimal('1'),
            sales_last_2_months=Decimal('10')
        )
        
        production_list = self.production_service.calculate_production_list()
        
        # Only products with production_needed > 0 should be in list
        for item in production_list.items.all():
            self.assertGreater(item.product.production_needed, Decimal('0'))
    
    def test_production_quantities_accuracy(self):
        """Test that production quantities match expected calculations."""
        # Test specific calculation scenarios
        
        # Scenario 1: Critical product
        critical = ProductFactory.create_critical_product(
            article='CALC-001',
            current_stock=Decimal('2'),
            sales_last_2_months=Decimal('10')
        )
        self.assertEqual(critical.production_needed, Decimal('8'))  # 10 - 2
        
        # Scenario 2: New product  
        new = ProductFactory.create_new_product(
            article='CALC-002',
            current_stock=Decimal('3'),
            sales_last_2_months=Decimal('0')
        )
        self.assertEqual(new.production_needed, Decimal('7'))  # 10 - 3
        
        # Scenario 3: Old product with low sales
        old_low = ProductFactory.create_old_product_low_sales(
            article='CALC-003',
            current_stock=Decimal('6'),
            sales_last_2_months=Decimal('2')
        )
        self.assertEqual(old_low.production_needed, Decimal('4'))  # 10 - 6
        
        # Create production list and verify quantities
        production_list = self.production_service.calculate_production_list(
            apply_coefficients=False  # No coefficients for direct comparison
        )
        
        for item in production_list.items.all():
            # Quantity should match production_needed when no coefficients applied
            self.assertEqual(item.quantity, item.product.production_needed)
    
    def test_production_list_ordering(self):
        """Test that production list items are properly ordered by priority."""
        # Create products with different priorities
        products = [
            ProductFactory.create_critical_product(article='PRI-100', current_stock=1, sales_last_2_months=10),
            ProductFactory.create_old_product_medium_sales(article='PRI-080', current_stock=3, sales_last_2_months=15), 
            ProductFactory.create_new_product(article='PRI-060', current_stock=2, sales_last_2_months=0),
            ProductFactory.create_old_product_low_sales(article='PRI-040', current_stock=7, sales_last_2_months=2),
        ]
        
        production_list = self.production_service.calculate_production_list()
        
        # Check that items are ordered by priority (highest first)
        items = list(production_list.items.all())
        if len(items) > 1:
            for i in range(len(items) - 1):
                current_priority = items[i].product.production_priority
                next_priority = items[i + 1].product.production_priority
                # Current priority should be >= next priority
                self.assertGreaterEqual(current_priority, next_priority)