from django.urls import path
from .views import sync_status, sync_history, sync_warehouses, sync_product_groups, start_sync, download_images, download_specific_images, test_moysklad_data, test_connection

urlpatterns = [
    path('start/', start_sync, name='start-sync'),
    path('status/', sync_status, name='sync-status'),
    path('history/', sync_history, name='sync-history'),
    path('warehouses/', sync_warehouses, name='sync-warehouses'),
    path('product-groups/', sync_product_groups, name='sync-product-groups'),
    path('download-images/', download_images, name='download-images'),
    path('download-specific-images/', download_specific_images, name='download-specific-images'),
    path('test-moysklad-data/', test_moysklad_data, name='test-moysklad-data'),
    path('test-connection/', test_connection, name='test-connection'),
]