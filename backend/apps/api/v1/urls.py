from django.urls import path, include

urlpatterns = [
    path('products/', include('apps.products.urls')),
    path('sync/', include('apps.sync.urls')),
    path('reports/', include('apps.reports.urls')),
    path('settings/', include('apps.settings.urls')),
    # path('monitoring/', include('apps.monitoring.urls')),  # Temporarily disabled
]