"""
Integration between products app and monitoring system.
"""
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from apps.products.models import Product
from apps.monitoring.services import AlgorithmMonitor


# Context manager for monitoring algorithm executions
class MonitoredAlgorithmExecution:
    """Context manager for monitoring algorithm executions."""
    
    def __init__(self, execution_type: str, products_count: int = 0):
        self.execution_type = execution_type
        self.products_count = products_count
        self.monitor = AlgorithmMonitor()
        self.execution = None
        self.errors_count = 0
        self.error_details = ""
    
    def __enter__(self):
        self.execution = self.monitor.start_monitoring(self.execution_type, self.products_count)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            self.errors_count = 1
            self.error_details = f"{exc_type.__name__}: {str(exc_val)}"
        
        # Calculate results
        products_needing_production = Product.objects.filter(production_needed__gt=0).count()
        total_production_units = sum(
            p.production_needed for p in Product.objects.filter(production_needed__gt=0)
        )
        
        self.monitor.finish_monitoring(
            products_needing_production=products_needing_production,
            total_production_units=total_production_units,
            errors_count=self.errors_count,
            error_details=self.error_details
        )
        
        # Don't suppress exceptions
        return False


# Signal handlers for automatic monitoring
@receiver(post_save, sender=Product)
def monitor_product_calculation(sender, instance, created, **kwargs):
    """Monitor individual product calculations."""
    if created:
        # New product created - run monitoring
        try:
            with MonitoredAlgorithmExecution('single_product', 1):
                # Trigger calculation
                instance.update_calculated_fields()
                instance.save(update_fields=['production_needed', 'production_priority', 'product_type'])
        except Exception:
            # Don't break product creation if monitoring fails
            pass