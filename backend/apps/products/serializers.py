from rest_framework import serializers
from .models import Product, ProductImage

class ProductImageSerializer(serializers.ModelSerializer):
    """
    Serializer for product images.
    """
    class Meta:
        model = ProductImage
        fields = ['id', 'image', 'thumbnail', 'moysklad_url', 'is_main', 'created_at']

class ProductListSerializer(serializers.ModelSerializer):
    """
    Simplified serializer for product list view.
    """
    main_image = serializers.SerializerMethodField()
    images = serializers.SerializerMethodField()
    
    class Meta:
        model = Product
        fields = [
            'id', 'article', 'name', 'product_type', 
            'current_stock', 'sales_last_2_months', 'average_daily_consumption',
            'production_needed', 'production_priority',
            'days_of_stock', 'main_image', 'images', 'last_synced_at'
        ]
    
    def get_main_image(self, obj):
        main_image = obj.images.filter(is_main=True).first()
        if main_image and main_image.thumbnail:
            return self.context['request'].build_absolute_uri(main_image.thumbnail.url)
        return None
    
    def get_images(self, obj):
        """Get all images for the product."""
        request = self.context.get('request')
        if not request:
            return []
        
        images = []
        for img in obj.images.all():
            image_data = {
                'id': img.id,
                'is_main': img.is_main,
                'image': request.build_absolute_uri(img.image.url) if img.image else None,
                'thumbnail': request.build_absolute_uri(img.thumbnail.url) if img.thumbnail else None,
            }
            images.append(image_data)
        return images

class ProductDetailSerializer(serializers.ModelSerializer):
    """
    Detailed serializer for product detail view.
    """
    images = ProductImageSerializer(many=True, read_only=True)
    
    class Meta:
        model = Product
        fields = [
            'id', 'moysklad_id', 'article', 'name', 'description',
            'product_group_id', 'product_group_name',
            'current_stock', 'sales_last_2_months', 'average_daily_consumption',
            'product_type', 'days_of_stock', 'production_needed', 'production_priority',
            'images', 'created_at', 'updated_at', 'last_synced_at'
        ]

class ProductStatsSerializer(serializers.Serializer):
    """
    Serializer for product statistics.
    """
    total_products = serializers.IntegerField()
    new_products = serializers.IntegerField()
    old_products = serializers.IntegerField()
    critical_products = serializers.IntegerField()
    production_needed_items = serializers.IntegerField()
    total_production_units = serializers.DecimalField(max_digits=10, decimal_places=2)