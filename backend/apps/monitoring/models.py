"""
Monitoring models for tracking algorithm behavior and system health.
"""
from django.db import models
from django.utils import timezone
from decimal import Decimal
import json


class AlgorithmExecution(models.Model):
    """Track algorithm execution for monitoring and alerting."""
    
    EXECUTION_TYPE_CHOICES = [
        ('single_product', 'Single Product Calculation'),
        ('batch_recalculation', 'Batch Recalculation'),
        ('production_list', 'Production List Generation'),
        ('monitoring_check', 'Monitoring Health Check'),
    ]
    
    execution_type = models.CharField(max_length=20, choices=EXECUTION_TYPE_CHOICES)
    started_at = models.DateTimeField(auto_now_add=True)
    finished_at = models.DateTimeField(null=True, blank=True)
    duration_seconds = models.DecimalField(max_digits=10, decimal_places=3, null=True)
    
    # Algorithm inputs and outputs
    products_processed = models.IntegerField(default=0)
    products_needing_production = models.IntegerField(default=0)
    total_production_units = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    # Performance metrics
    average_calculation_time_ms = models.DecimalField(max_digits=8, decimal_places=2, null=True)
    memory_usage_mb = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    database_queries = models.IntegerField(default=0)
    
    # Error tracking
    errors_encountered = models.IntegerField(default=0)
    error_details = models.TextField(blank=True)
    
    # Algorithm version/checksum for change detection
    algorithm_version = models.CharField(max_length=64, blank=True)  # Git commit hash or version
    
    class Meta:
        ordering = ['-started_at']
        indexes = [
            models.Index(fields=['execution_type', 'started_at']),
            models.Index(fields=['algorithm_version']),
        ]
    
    def __str__(self):
        return f"{self.execution_type} - {self.started_at.strftime('%Y-%m-%d %H:%M:%S')}"
    
    def mark_finished(self):
        """Mark execution as finished and calculate duration."""
        self.finished_at = timezone.now()
        if self.started_at:
            delta = self.finished_at - self.started_at
            self.duration_seconds = Decimal(str(delta.total_seconds()))
        self.save()


class AlgorithmBaseline(models.Model):
    """Store baseline test results for regression detection."""
    
    test_case_name = models.CharField(max_length=100)
    
    # Test inputs
    article = models.CharField(max_length=255)
    current_stock = models.DecimalField(max_digits=10, decimal_places=2)
    sales_last_2_months = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Expected outputs
    expected_production_need = models.DecimalField(max_digits=10, decimal_places=2)
    expected_product_type = models.CharField(max_length=20)
    expected_priority = models.IntegerField()
    
    # Test metadata
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    description = models.TextField(blank=True)
    
    class Meta:
        ordering = ['test_case_name']
        unique_together = ['test_case_name', 'article']
    
    def __str__(self):
        return f"{self.test_case_name}: {self.article}"


class AlgorithmAlert(models.Model):
    """Track alerts related to algorithm behavior."""
    
    ALERT_TYPE_CHOICES = [
        ('regression', 'Algorithm Regression'),
        ('performance', 'Performance Degradation'),
        ('anomaly', 'Data Anomaly'),
        ('error', 'Execution Error'),
        ('change', 'Algorithm Change'),
    ]
    
    SEVERITY_CHOICES = [
        ('critical', 'Critical'),
        ('high', 'High'),
        ('medium', 'Medium'),
        ('low', 'Low'),
    ]
    
    STATUS_CHOICES = [
        ('open', 'Open'),
        ('acknowledged', 'Acknowledged'),
        ('investigating', 'Investigating'),
        ('resolved', 'Resolved'),
        ('false_positive', 'False Positive'),
    ]
    
    alert_type = models.CharField(max_length=20, choices=ALERT_TYPE_CHOICES)
    severity = models.CharField(max_length=10, choices=SEVERITY_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='open')
    
    title = models.CharField(max_length=255)
    description = models.TextField()
    details = models.JSONField(default=dict)
    
    # Timing
    created_at = models.DateTimeField(auto_now_add=True)
    acknowledged_at = models.DateTimeField(null=True, blank=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    
    # Related data
    execution = models.ForeignKey(AlgorithmExecution, on_delete=models.CASCADE, null=True, blank=True)
    
    # Notification tracking
    notifications_sent = models.JSONField(default=list)  # List of notification channels used
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['alert_type', 'status']),
            models.Index(fields=['severity', 'created_at']),
        ]
    
    def __str__(self):
        return f"[{self.severity.upper()}] {self.title}"
    
    def acknowledge(self, user=None):
        """Acknowledge the alert."""
        self.status = 'acknowledged'
        self.acknowledged_at = timezone.now()
        self.save()
    
    def resolve(self, resolution_note=""):
        """Mark alert as resolved."""
        self.status = 'resolved'
        self.resolved_at = timezone.now()
        if resolution_note:
            self.details['resolution_note'] = resolution_note
        self.save()


class SystemHealth(models.Model):
    """Track overall system health metrics."""
    
    timestamp = models.DateTimeField(auto_now_add=True)
    
    # API health
    api_response_time_ms = models.DecimalField(max_digits=8, decimal_places=2, null=True)
    api_error_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)  # Percentage
    
    # Database health
    database_connection_time_ms = models.DecimalField(max_digits=8, decimal_places=2, null=True)
    database_query_time_avg_ms = models.DecimalField(max_digits=8, decimal_places=2, null=True)
    database_connections_active = models.IntegerField(default=0)
    
    # Redis health
    redis_response_time_ms = models.DecimalField(max_digits=8, decimal_places=2, null=True)
    redis_memory_usage_mb = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    
    # Application metrics
    total_products = models.IntegerField(default=0)
    products_needing_production = models.IntegerField(default=0)
    avg_calculation_time_ms = models.DecimalField(max_digits=8, decimal_places=2, null=True)
    
    # System resources
    memory_usage_percent = models.DecimalField(max_digits=5, decimal_places=2, null=True)
    cpu_usage_percent = models.DecimalField(max_digits=5, decimal_places=2, null=True)
    disk_usage_percent = models.DecimalField(max_digits=5, decimal_places=2, null=True)
    
    # Overall health status
    is_healthy = models.BooleanField(default=True)
    health_score = models.DecimalField(max_digits=5, decimal_places=2, default=100)  # 0-100
    
    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['timestamp', 'is_healthy']),
        ]
    
    def __str__(self):
        status = "Healthy" if self.is_healthy else "Unhealthy"
        return f"System Health [{status}] - {self.timestamp.strftime('%Y-%m-%d %H:%M:%S')}"


class ProductionListAudit(models.Model):
    """Audit trail for production list changes."""
    
    ACTION_CHOICES = [
        ('created', 'Created'),
        ('modified', 'Modified'),
        ('deleted', 'Deleted'),
        ('exported', 'Exported'),
    ]
    
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    # Production list data
    production_list_id = models.IntegerField()
    total_items_before = models.IntegerField(null=True)
    total_items_after = models.IntegerField(null=True)
    total_units_before = models.DecimalField(max_digits=12, decimal_places=2, null=True)
    total_units_after = models.DecimalField(max_digits=12, decimal_places=2, null=True)
    
    # Change details
    changes_summary = models.JSONField(default=dict)  # Summary of what changed
    algorithm_version = models.CharField(max_length=64, blank=True)
    
    # User context (if available)
    user_id = models.CharField(max_length=100, blank=True)
    user_agent = models.CharField(max_length=255, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    
    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['production_list_id', 'timestamp']),
            models.Index(fields=['action', 'timestamp']),
        ]
    
    def __str__(self):
        return f"Production List {self.production_list_id} - {self.action} at {self.timestamp}"