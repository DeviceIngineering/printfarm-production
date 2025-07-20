from django.db import models
from apps.core.models import TimestampedModel
from apps.products.models import Product

class SyncLog(models.Model):
    """
    Sync log model for tracking synchronization operations.
    """
    SYNC_TYPE_CHOICES = [
        ('manual', 'Ручная'),
        ('scheduled', 'По расписанию'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'В процессе'),
        ('success', 'Успешно'),
        ('failed', 'Ошибка'),
        ('partial', 'Частично выполнено'),
    ]
    
    sync_type = models.CharField(max_length=20, choices=SYNC_TYPE_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    started_at = models.DateTimeField(auto_now_add=True)
    finished_at = models.DateTimeField(null=True, blank=True)
    
    warehouse_id = models.CharField(max_length=36)
    warehouse_name = models.CharField(max_length=255)
    
    excluded_groups = models.JSONField(default=list)
    
    total_products = models.IntegerField(default=0)
    synced_products = models.IntegerField(default=0)
    failed_products = models.IntegerField(default=0)
    
    current_article = models.CharField(max_length=255, blank=True, null=True)
    
    error_details = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-started_at']
    
    def __str__(self):
        return f"Sync {self.id} - {self.status} ({self.started_at})"
    
    @property
    def duration(self):
        """
        Calculate sync duration if finished.
        """
        if self.finished_at:
            return self.finished_at - self.started_at
        return None
    
    @property
    def success_rate(self):
        """
        Calculate success rate percentage.
        """
        if self.total_products > 0:
            return (self.synced_products / self.total_products) * 100
        return 0

class ProductionList(TimestampedModel):
    """
    Production list model for storing generated production lists.
    """
    created_by = models.CharField(max_length=255, default='system')
    
    total_items = models.IntegerField(default=0)
    total_units = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    export_file = models.FileField(upload_to='exports/', null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Production List {self.id} - {self.created_at.date()}"

class ProductionListItem(models.Model):
    """
    Individual items in a production list.
    """
    production_list = models.ForeignKey(ProductionList, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    
    quantity = models.DecimalField(max_digits=10, decimal_places=2)
    priority = models.IntegerField()
    
    class Meta:
        ordering = ['priority', 'product__article']
    
    def __str__(self):
        return f"{self.product.article} - {self.quantity}"
