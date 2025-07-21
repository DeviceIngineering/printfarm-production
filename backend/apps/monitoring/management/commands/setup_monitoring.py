"""
Management command to setup monitoring baselines and health checks.
"""
from django.core.management.base import BaseCommand
from decimal import Decimal
from apps.monitoring.models import AlgorithmBaseline
from apps.monitoring.services import AlgorithmMonitor, SystemHealthMonitor


class Command(BaseCommand):
    help = 'Setup monitoring baselines and health checks for PrintFarm'

    def add_arguments(self, parser):
        parser.add_argument(
            '--create-baselines',
            action='store_true',
            help='Create algorithm baseline test cases',
        )
        parser.add_argument(
            '--run-health-check',
            action='store_true',
            help='Run system health check',
        )
        parser.add_argument(
            '--run-regression-test',
            action='store_true',
            help='Run algorithm regression test',
        )

    def handle(self, *args, **options):
        if options['create_baselines']:
            self.create_baselines()
        
        if options['run_health_check']:
            self.run_health_check()
        
        if options['run_regression_test']:
            self.run_regression_test()
        
        if not any([options['create_baselines'], options['run_health_check'], options['run_regression_test']]):
            self.stdout.write("No action specified. Use --help for options.")

    def create_baselines(self):
        """Create algorithm baseline test cases."""
        self.stdout.write("Creating algorithm baseline test cases...")
        
        # Clear existing baselines
        AlgorithmBaseline.objects.all().delete()
        
        # Create baseline test cases based on our conversation examples
        baselines = [
            {
                'test_case_name': 'conversation_case_1',
                'article': '375-42108',
                'current_stock': Decimal('2'),
                'sales_last_2_months': Decimal('10'),
                'expected_production_need': Decimal('8'),
                'expected_product_type': 'critical',
                'expected_priority': 100,
                'description': 'Test case from conversation - critical product with low stock'
            },
            {
                'test_case_name': 'conversation_case_2', 
                'article': '381-40801',
                'current_stock': Decimal('8'),
                'sales_last_2_months': Decimal('2'),
                'expected_production_need': Decimal('2'),
                'expected_product_type': 'old',
                'expected_priority': 20,
                'description': 'Test case from conversation - old product with low sales'
            },
            {
                'test_case_name': 'new_product_low_stock',
                'article': 'NEW-001',
                'current_stock': Decimal('3'),
                'sales_last_2_months': Decimal('0'),
                'expected_production_need': Decimal('7'),
                'expected_product_type': 'new',
                'expected_priority': 60,
                'description': 'New product with low stock should get production'
            },
            {
                'test_case_name': 'new_product_sufficient_stock',
                'article': 'NEW-002',
                'current_stock': Decimal('12'),
                'sales_last_2_months': Decimal('0'),
                'expected_production_need': Decimal('0'),
                'expected_product_type': 'new',
                'expected_priority': 20,
                'description': 'New product with sufficient stock should not need production'
            },
            {
                'test_case_name': 'old_product_high_sales',
                'article': 'OLD-001',
                'current_stock': Decimal('3'),
                'sales_last_2_months': Decimal('25'),
                'expected_production_need': Decimal('9'),  # This will depend on exact calculation
                'expected_product_type': 'critical',
                'expected_priority': 100,
                'description': 'Old product with high sales and low stock'
            },
            {
                'test_case_name': 'edge_case_zero_stock',
                'article': 'EDGE-001',
                'current_stock': Decimal('0'),
                'sales_last_2_months': Decimal('15'),
                'expected_production_need': Decimal('10'),
                'expected_product_type': 'critical',
                'expected_priority': 100,
                'description': 'Edge case with zero stock'
            },
        ]
        
        created_count = 0
        for baseline_data in baselines:
            baseline, created = AlgorithmBaseline.objects.get_or_create(
                test_case_name=baseline_data['test_case_name'],
                article=baseline_data['article'],
                defaults=baseline_data
            )
            if created:
                created_count += 1
                self.stdout.write(f"  ✅ Created baseline: {baseline.test_case_name}")
            else:
                self.stdout.write(f"  ⚠️  Baseline already exists: {baseline.test_case_name}")
        
        self.stdout.write(
            self.style.SUCCESS(f"✅ Created {created_count} new baseline test cases")
        )

    def run_health_check(self):
        """Run system health check."""
        self.stdout.write("Running system health check...")
        
        try:
            health_monitor = SystemHealthMonitor()
            health = health_monitor.collect_health_metrics()
            
            status = "HEALTHY" if health.is_healthy else "UNHEALTHY"
            style = self.style.SUCCESS if health.is_healthy else self.style.ERROR
            
            self.stdout.write(style(f"System Status: {status}"))
            self.stdout.write(f"Health Score: {health.health_score}%")
            self.stdout.write(f"API Response Time: {health.api_response_time_ms}ms")
            self.stdout.write(f"Database Connection Time: {health.database_connection_time_ms}ms")
            self.stdout.write(f"Memory Usage: {health.memory_usage_percent}%")
            self.stdout.write(f"CPU Usage: {health.cpu_usage_percent}%")
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"❌ Health check failed: {e}")
            )

    def run_regression_test(self):
        """Run algorithm regression test."""
        self.stdout.write("Running algorithm regression tests...")
        
        try:
            monitor = AlgorithmMonitor()
            results = monitor.run_regression_tests()
            
            if results['all_passed']:
                self.stdout.write(
                    self.style.SUCCESS(f"✅ All {results['total_tests']} regression tests passed!")
                )
            else:
                self.stdout.write(
                    self.style.ERROR(f"❌ {results['failed_tests']} of {results['total_tests']} tests failed!")
                )
                
                # Show failed tests
                for result in results['results']:
                    if not result['passed']:
                        self.stdout.write(f"  ❌ {result['test_case']} ({result['article']}):")
                        
                        if not result['production_need']['match']:
                            self.stdout.write(
                                f"    Production need: expected {result['production_need']['expected']}, "
                                f"got {result['production_need']['actual']}"
                            )
                        
                        if not result['product_type']['match']:
                            self.stdout.write(
                                f"    Product type: expected {result['product_type']['expected']}, "
                                f"got {result['product_type']['actual']}"
                            )
                        
                        if not result['priority']['match']:
                            self.stdout.write(
                                f"    Priority: expected {result['priority']['expected']}, "
                                f"got {result['priority']['actual']}"
                            )
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"❌ Regression test failed: {e}")
            )