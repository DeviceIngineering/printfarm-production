from django.urls import path, include
from .tochka_views import get_products_for_tochka, get_production_list_for_tochka, get_products_stats_for_tochka

urlpatterns = [
    path('products/', include('apps.products.urls')),
    path('sync/', include('apps.sync.urls')),
    path('reports/', include('apps.reports.urls')),
    path('settings/', include('apps.settings.urls')),
    # path('monitoring/', include('apps.monitoring.urls')),  # Temporarily disabled
    
    # Tochka API endpoints
    path('tochka/products/', get_products_for_tochka, name='tochka-products'),
    path('tochka/production/', get_production_list_for_tochka, name='tochka-production'),
    path('tochka/stats/', get_products_stats_for_tochka, name='tochka-stats'),
]