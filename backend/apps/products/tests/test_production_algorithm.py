"""
Tests for production calculation algorithm.
"""
from decimal import Decimal
from django.test import TestCase
from apps.products.models import Product


class ProductionAlgorithmTestCase(TestCase):
    """Test cases for production calculation algorithm."""
    
    def setUp(self):
        """Set up test data."""
        pass
    
    def create_product(self, article, current_stock, sales_last_2_months, **kwargs):
        """Helper method to create a product with test data."""
        defaults = {
            'moysklad_id': f'test-{article}',
            'name': f'Test Product {article}',
            'description': 'Test product for algorithm testing',
        }
        defaults.update(kwargs)
        
        product = Product.objects.create(
            article=article,
            current_stock=Decimal(str(current_stock)),
            sales_last_2_months=Decimal(str(sales_last_2_months)),
            **defaults
        )
        product.update_calculated_fields()
        product.save()
        return product
    
    def test_critical_product_classification(self):
        """Test critical product classification: low stock + has sales."""
        product = self.create_product(
            article='CRIT-001',
            current_stock=2,
            sales_last_2_months=10
        )
        
        self.assertEqual(product.product_type, 'critical')
        self.assertEqual(product.production_needed, Decimal('8'))  # 10 - 2 = 8
        self.assertEqual(product.production_priority, 100)
    
    def test_new_product_no_sales(self):
        """Test new product with no sales."""
        product = self.create_product(
            article='NEW-001',
            current_stock=3,
            sales_last_2_months=0
        )
        
        self.assertEqual(product.product_type, 'new')
        self.assertEqual(product.production_needed, Decimal('7'))  # 10 - 3 = 7
        self.assertEqual(product.production_priority, 60)
    
    def test_new_product_low_sales_low_stock(self):
        """Test new product with low sales and low stock."""
        product = self.create_product(
            article='NEW-002',
            current_stock=2,
            sales_last_2_months=3
        )
        
        self.assertEqual(product.classify_product_type(), 'critical')  # Low stock + sales
        self.assertEqual(product.production_needed, Decimal('8'))  # 10 - 2 = 8
    
    def test_new_product_sufficient_stock(self):
        """Test new product with sufficient stock."""
        product = self.create_product(
            article='NEW-003',
            current_stock=12,
            sales_last_2_months=0
        )
        
        self.assertEqual(product.product_type, 'new')
        self.assertEqual(product.production_needed, Decimal('0'))  # No production needed
    
    def test_old_product_low_sales(self):
        """Test old product with low sales (<=3)."""
        product = self.create_product(
            article='OLD-001',
            current_stock=8,
            sales_last_2_months=2
        )
        
        self.assertEqual(product.product_type, 'old')
        self.assertEqual(product.production_needed, Decimal('2'))  # 10 - 8 = 2
        
        # Test different stock levels
        product2 = self.create_product(
            article='OLD-002',
            current_stock=5,
            sales_last_2_months=3
        )
        self.assertEqual(product2.production_needed, Decimal('5'))  # 10 - 5 = 5
    
    def test_old_product_medium_sales(self):
        """Test old product with medium sales (3 < sales <= 10)."""
        # Test exact boundary: sales = 10, stock <= 6
        product = self.create_product(
            article='OLD-003',
            current_stock=2,
            sales_last_2_months=10
        )
        
        self.assertEqual(product.product_type, 'critical')  # Stock < 5 and has sales
        self.assertEqual(product.production_needed, Decimal('8'))  # 10 - 2 = 8
        
        # Test medium sales with stock <= 6
        product2 = self.create_product(
            article='OLD-004',
            current_stock=6,
            sales_last_2_months=5
        )
        
        self.assertEqual(product2.product_type, 'old')
        self.assertEqual(product2.production_needed, Decimal('4'))  # 10 - 6 = 4
        
        # Test medium sales with stock > 6 (should not need production)
        product3 = self.create_product(
            article='OLD-005',
            current_stock=8,
            sales_last_2_months=5
        )
        
        self.assertEqual(product3.production_needed, Decimal('0'))
    
    def test_old_product_high_sales(self):
        """Test old product with high sales (> 10)."""
        product = self.create_product(
            article='OLD-006',
            current_stock=5,
            sales_last_2_months=20
        )
        
        # Average daily consumption: 20/60 = 0.333...
        # Target stock: 0.333... * 15 = 5.0
        # Current stock: 5, target: 5, so production needed: 0
        
        self.assertEqual(product.classify_product_type(), 'old')  # Stock >= 5 and sales > 0
        
        # Let's test with lower stock
        product2 = self.create_product(
            article='OLD-007',
            current_stock=2,
            sales_last_2_months=30
        )
        
        # Average daily: 30/60 = 0.5
        # Target stock: 0.5 * 15 = 7.5
        # But first check: stock < average_daily * 10? 2 < 0.5 * 10 = 5? Yes
        # So production needed: 7.5 - 2 = 5.5
        
        expected_daily = Decimal('30') / Decimal('60')
        expected_target = expected_daily * Decimal('15')
        expected_production = expected_target - Decimal('2')
        
        self.assertEqual(product2.product_type, 'critical')
        self.assertAlmostEqual(float(product2.production_needed), float(expected_production), places=2)
    
    def test_days_of_stock_calculation(self):
        """Test days of stock calculation."""
        product = self.create_product(
            article='DAYS-001',
            current_stock=10,
            sales_last_2_months=30
        )
        
        # Average daily: 30/60 = 0.5
        # Days of stock: 10 / 0.5 = 20 days
        expected_days = Decimal('10') / (Decimal('30') / Decimal('60'))
        
        self.assertAlmostEqual(float(product.days_of_stock), float(expected_days), places=2)
    
    def test_priority_calculation(self):
        """Test priority calculation logic."""
        # Critical with low stock
        critical_product = self.create_product(
            article='PRIO-001',
            current_stock=2,
            sales_last_2_months=10
        )
        self.assertEqual(critical_product.production_priority, 100)
        
        # New with low stock
        new_product = self.create_product(
            article='PRIO-002',
            current_stock=3,
            sales_last_2_months=0
        )
        self.assertEqual(new_product.production_priority, 60)
        
        # Critical with very low stock (stock < 5 + sales > 0 = critical)
        old_product_low = self.create_product(
            article='PRIO-003',
            current_stock=2,
            sales_last_2_months=30  # This gives ~4 days of stock
        )
        self.assertEqual(old_product_low.production_priority, 100)  # Critical priority
        
        # Old with medium days of stock  
        old_product_medium = self.create_product(
            article='PRIO-004',
            current_stock=5,
            sales_last_2_months=30  # This gives 10 days of stock (5 / 0.5)
        )
        # Since days_of_stock = 10, it doesn't meet < 10 condition, so priority = 20
        self.assertEqual(old_product_medium.production_priority, 20)
    
    def test_edge_cases(self):
        """Test edge cases and boundary conditions."""
        # Zero stock
        zero_stock = self.create_product(
            article='EDGE-001',
            current_stock=0,
            sales_last_2_months=5
        )
        self.assertEqual(zero_stock.product_type, 'critical')
        self.assertEqual(zero_stock.production_needed, Decimal('10'))
        
        # Exact boundary: stock = 5, sales > 0
        boundary_product = self.create_product(
            article='EDGE-002',
            current_stock=5,
            sales_last_2_months=1
        )
        self.assertEqual(boundary_product.product_type, 'old')  # stock >= 5
        
        # High stock, no production needed
        high_stock = self.create_product(
            article='EDGE-003',
            current_stock=100,
            sales_last_2_months=2
        )
        self.assertEqual(high_stock.production_needed, Decimal('0'))
    
    def test_algorithm_consistency(self):
        """Test that algorithm produces consistent results."""
        # Test the specific cases mentioned in the issue
        
        # Case 1: Article 375-42108 - остаток 2, расход 10
        case1 = self.create_product(
            article='375-42108',
            current_stock=2,
            sales_last_2_months=10
        )
        self.assertGreater(case1.production_needed, Decimal('0'))
        self.assertEqual(case1.production_needed, Decimal('8'))  # 10 - 2
        
        # Case 2: Article 381-40801 - остаток 8, расход 2  
        case2 = self.create_product(
            article='381-40801',
            current_stock=8,
            sales_last_2_months=2
        )
        self.assertGreater(case2.production_needed, Decimal('0'))
        self.assertEqual(case2.production_needed, Decimal('2'))  # 10 - 8