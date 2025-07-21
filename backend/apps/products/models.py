from django.db import models
from decimal import Decimal
from apps.core.models import TimestampedModel

class Product(TimestampedModel):
    """
    Product model for storing МойСклад product data.
    """
    # Basic fields from МойСклад
    moysklad_id = models.CharField(max_length=36, unique=True, db_index=True)
    article = models.CharField(max_length=255, db_index=True)
    name = models.CharField(max_length=500)
    description = models.TextField(blank=True)
    
    # Product group
    product_group_id = models.CharField(max_length=36, blank=True)
    product_group_name = models.CharField(max_length=255, blank=True)
    
    # Stock and sales data
    current_stock = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0'))
    sales_last_2_months = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0'))
    average_daily_consumption = models.DecimalField(max_digits=10, decimal_places=4, default=Decimal('0'))
    
    # Classification
    PRODUCT_TYPE_CHOICES = [
        ('new', 'Новая позиция'),
        ('old', 'Старая позиция'),
        ('critical', 'Критическая позиция'),
    ]
    product_type = models.CharField(max_length=20, choices=PRODUCT_TYPE_CHOICES, default='new')
    
    # Calculated fields
    days_of_stock = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    production_needed = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0'))
    production_priority = models.IntegerField(default=0)
    
    # Sync metadata
    last_synced_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-production_priority', 'article']
        indexes = [
            models.Index(fields=['product_type', 'production_priority']),
            models.Index(fields=['current_stock', 'product_type']),
            models.Index(fields=['article']),
            models.Index(fields=['moysklad_id']),
        ]
    
    def __str__(self):
        return f"{self.article} - {self.name[:50]}"
    
    def classify_product_type(self):
        """
        Classify product based on stock and sales data.
        """
        # Check for critical first: low stock + has sales
        if self.current_stock < 5 and self.sales_last_2_months > 0:
            return 'critical'
        
        # Check for new: no sales OR (low sales AND low stock)
        if self.sales_last_2_months == 0:
            return 'new'
        elif self.sales_last_2_months < 5 and self.current_stock < 5:
            return 'new'
        
        # Everything else is old
        return 'old'
    
    def calculate_days_of_stock(self):
        """
        Calculate how many days of stock remain.
        """
        if self.average_daily_consumption > 0:
            return self.current_stock / self.average_daily_consumption
        return None
    
    def calculate_production_need(self) -> Decimal:
        """
        Calculate production need based on product type and consumption.
        """
        if self.product_type == 'new':
            if self.current_stock < 5:
                return Decimal('10') - self.current_stock
            return Decimal('0')
        
        elif self.product_type in ['old', 'critical']:
            # Новые расширенные условия для старых и критических товаров
            
            # Условие 1: Обороты <= 3 И остаток < 5 → целевой остаток 5
            if self.sales_last_2_months <= 3 and self.current_stock < 5:
                return max(Decimal('5') - self.current_stock, Decimal('0'))
            
            # Условие 2: Обороты > 3 но <= 10 И остаток <= 6 → целевой остаток 10
            elif 3 < self.sales_last_2_months <= 10 and self.current_stock <= 6:
                return max(Decimal('10') - self.current_stock, Decimal('0'))
            
            # Существующая логика для товаров с высокими оборотами (> 10)
            elif self.sales_last_2_months > 10:
                target_days = 15  # целевой запас на 15 дней
                target_stock = self.average_daily_consumption * target_days
                
                if self.current_stock < self.average_daily_consumption * 10:
                    return max(target_stock - self.current_stock, Decimal('0'))
        
        return Decimal('0')
    
    def calculate_priority(self) -> int:
        """
        Calculate production priority (higher = more important).
        """
        if self.product_type == 'critical' and self.current_stock < 5:
            return 100
        elif self.product_type == 'old' and self.days_of_stock and self.days_of_stock < 5:
            return 80
        elif self.product_type == 'new' and self.current_stock < 5:
            return 60
        elif self.product_type == 'old' and self.days_of_stock and self.days_of_stock < 10:
            return 40
        else:
            return 20
    
    def update_calculated_fields(self):
        """
        Update all calculated fields.
        """
        # Calculate average daily consumption first
        if self.sales_last_2_months > 0:
            self.average_daily_consumption = self.sales_last_2_months / Decimal('60')
        else:
            self.average_daily_consumption = Decimal('0')
            
        # Then calculate other fields that depend on it
        self.product_type = self.classify_product_type()
        self.days_of_stock = self.calculate_days_of_stock()
        self.production_needed = self.calculate_production_need()
        self.production_priority = self.calculate_priority()
    
    def save(self, *args, **kwargs):
        self.update_calculated_fields()
        super().save(*args, **kwargs)

class ProductImage(TimestampedModel):
    """
    Product image model for storing product photos.
    """
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='products/', null=True, blank=True)
    thumbnail = models.ImageField(upload_to='products/thumbnails/', null=True, blank=True)
    moysklad_url = models.URLField(max_length=500, blank=True)
    is_main = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['-is_main', 'created_at']
    
    def __str__(self):
        return f"Image for {self.product.article}"
