from django.urls import path
from .views import (
    ProductListView, ProductDetailView, product_stats,
    calculate_production_list, get_production_list, production_stats, recalculate_production,
    export_production_list_view, sync_product_images_view
)

urlpatterns = [
    path('', ProductListView.as_view(), name='product-list'),
    path('<int:pk>/', ProductDetailView.as_view(), name='product-detail'),
    path('stats/', product_stats, name='product-stats'),
    path('production/calculate/', calculate_production_list, name='calculate-production-list'),
    path('production/list/', get_production_list, name='get-production-list'),
    path('production/list/<int:list_id>/', get_production_list, name='get-production-list-by-id'),
    path('production/stats/', production_stats, name='production-stats'),
    path('production/recalculate/', recalculate_production, name='recalculate-production'),
    path('production/export/', export_production_list_view, name='export-production'),
    path('production/export/<int:list_id>/', export_production_list_view, name='export-production-by-id'),
    path('<int:pk>/sync-images/', sync_product_images_view, name='sync-product-images'),
]