from django.urls import path, include
from .tochka_views import (
    get_products_for_tochka, 
    get_production_list_for_tochka, 
    get_products_stats_for_tochka,
    upload_excel_file_for_tochka,
    merge_excel_with_products,
    get_filtered_production_list,
    export_deduplicated_excel,
    export_production_list,
    upload_and_auto_process_excel
)
from .health import (
    health_check,
    health_check_detailed,
    readiness_check,
    liveness_check
)

urlpatterns = [
    # Health check endpoints
    path('health/', health_check, name='health-check'),
    path('health/detailed/', health_check_detailed, name='health-check-detailed'),
    path('readiness/', readiness_check, name='readiness-check'),
    path('liveness/', liveness_check, name='liveness-check'),
    
    # Main API endpoints
    path('products/', include('apps.products.urls')),
    path('sync/', include('apps.sync.urls')),
    path('reports/', include('apps.reports.urls')),
    path('settings/', include('apps.settings.urls')),
    # path('monitoring/', include('apps.monitoring.urls')),  # Temporarily disabled
    
    # Tochka API endpoints
    path('tochka/products/', get_products_for_tochka, name='tochka-products'),
    path('tochka/production/', get_production_list_for_tochka, name='tochka-production'),
    path('tochka/stats/', get_products_stats_for_tochka, name='tochka-stats'),
    path('tochka/upload-excel/', upload_excel_file_for_tochka, name='tochka-upload-excel'),
    path('tochka/merge-with-products/', merge_excel_with_products, name='tochka-merge-with-products'),
    path('tochka/filtered-production/', get_filtered_production_list, name='tochka-filtered-production'),
    path('tochka/export-deduplicated/', export_deduplicated_excel, name='tochka-export-deduplicated'),
    path('tochka/export-production/', export_production_list, name='tochka-export-production'),
    path('tochka/upload-and-auto-process/', upload_and_auto_process_excel, name='tochka-upload-and-auto-process'),
]