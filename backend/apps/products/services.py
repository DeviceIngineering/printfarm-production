"""
Production services for PrintFarm production system.
"""
import logging
from decimal import Decimal
from typing import List, Dict, Optional
from django.db.models import Q, F, Sum, Count

from .models import Product
from apps.sync.models import ProductionList, ProductionListItem

logger = logging.getLogger(__name__)

class ProductionService:
    """
    Service for calculating and managing production lists.
    """
    
    def calculate_production_list(self, min_priority: int = 20, apply_coefficients: bool = True) -> ProductionList:
        """
        Calculate and create a new production list.
        
        Args:
            min_priority: Minimum priority threshold for products
            apply_coefficients: Whether to apply assortment coefficients
        
        Returns:
            ProductionList: Created production list
        """
        # Get products that need production
        products_needing_production = Product.objects.filter(
            production_needed__gt=0,
            production_priority__gte=min_priority
        ).order_by('-production_priority', 'article')
        
        if not products_needing_production.exists():
            logger.info("No products need production")
            return self._create_empty_production_list()
        
        # Create production list
        production_list = ProductionList.objects.create()
        
        # Determine if we should apply assortment strategy
        total_items = products_needing_production.count()
        use_assortment_strategy = total_items >= 30
        
        logger.info(f"Creating production list with {total_items} items, "
                   f"assortment strategy: {use_assortment_strategy}")
        
        # Process products
        total_units = Decimal('0')
        priority_order = 1
        
        for product in products_needing_production:
            quantity = self._calculate_production_quantity(
                product, 
                use_assortment_strategy and apply_coefficients
            )
            
            if quantity > 0:
                ProductionListItem.objects.create(
                    production_list=production_list,
                    product=product,
                    quantity=quantity,
                    priority=priority_order
                )
                
                total_units += quantity
                priority_order += 1
        
        # Update production list totals
        production_list.total_items = priority_order - 1
        production_list.total_units = total_units
        production_list.save()
        
        logger.info(f"Production list created: {production_list.total_items} items, "
                   f"{production_list.total_units} total units")
        
        return production_list
    
    def _calculate_production_quantity(self, product: Product, apply_coefficient: bool = True) -> Decimal:
        """
        Calculate production quantity for a product.
        
        Args:
            product: Product instance
            apply_coefficient: Whether to apply assortment coefficients
        
        Returns:
            Decimal: Calculated production quantity
        """
        base_quantity = product.production_needed
        
        if not apply_coefficient:
            return base_quantity
        
        # Apply coefficients based on priority
        if product.production_priority >= 80:
            coefficient = Decimal('1.0')  # 100% of need
        elif product.production_priority >= 60:
            coefficient = Decimal('0.7')  # 70% of need
        elif product.production_priority >= 40:
            coefficient = Decimal('0.5')  # 50% of need
        else:
            coefficient = Decimal('0.3')  # 30% of need
        
        return base_quantity * coefficient
    
    def _create_empty_production_list(self) -> ProductionList:
        """
        Create an empty production list.
        """
        return ProductionList.objects.create(
            total_items=0,
            total_units=Decimal('0')
        )
    
    def get_production_list_data(self, production_list: ProductionList) -> Dict:
        """
        Get formatted data for a production list.
        """
        items = ProductionListItem.objects.filter(
            production_list=production_list
        ).select_related('product').order_by('priority')
        
        items_data = []
        for item in items:
            items_data.append({
                'priority': item.priority,
                'article': item.product.article,
                'name': item.product.name,
                'current_stock': float(item.product.current_stock),
                'quantity': float(item.quantity),
                'product_type': item.product.product_type,
                'production_priority': item.product.production_priority,
                'group_name': item.product.product_group_name,
            })
        
        return {
            'id': production_list.id,
            'created_at': production_list.created_at,
            'total_items': production_list.total_items,
            'total_units': float(production_list.total_units),
            'items': items_data
        }
    
    def get_production_stats(self) -> Dict:
        """
        Get production statistics.
        """
        products_needing_production = Product.objects.filter(production_needed__gt=0)
        
        stats = {
            'total_products_needing_production': products_needing_production.count(),
            'critical_priority_count': products_needing_production.filter(production_priority__gte=80).count(),
            'high_priority_count': products_needing_production.filter(production_priority__range=(60, 79)).count(),
            'medium_priority_count': products_needing_production.filter(production_priority__range=(40, 59)).count(),
            'low_priority_count': products_needing_production.filter(production_priority__lt=40).count(),
            'total_units_needed': products_needing_production.aggregate(
                total=Sum('production_needed')
            )['total'] or Decimal('0'),
        }
        
        # Add breakdown by product type
        type_stats = products_needing_production.values('product_type').annotate(
            count=Count('id'),
            total_needed=Sum('production_needed')
        )
        
        stats['by_type'] = {
            item['product_type']: {
                'count': item['count'],
                'total_needed': float(item['total_needed'] or 0)
            }
            for item in type_stats
        }
        
        return stats
    
    def recalculate_all_products(self) -> Dict:
        """
        Recalculate production needs for all products.
        """
        products = Product.objects.all()
        updated_count = 0
        
        for product in products:
            old_priority = product.production_priority
            old_needed = product.production_needed
            
            # Trigger recalculation
            product.update_calculated_fields()
            
            if (product.production_priority != old_priority or 
                product.production_needed != old_needed):
                product.save()
                updated_count += 1
        
        logger.info(f"Recalculated {updated_count} products")
        
        return {
            'total_products': products.count(),
            'updated_products': updated_count,
            'stats': self.get_production_stats()
        }