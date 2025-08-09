from django.urls import path, include
from rest_framework.routers import DefaultRouter
from django.http import JsonResponse

def api_status(request):
    """API status endpoint"""
    return JsonResponse({
        'status': 'online',
        'version': '1.0.0',
        'service': 'PrintFarm API'
    })

urlpatterns = [
    path('', api_status, name='api-status'),
    path('products/', include('apps.products.urls')),
    path('sync/', include('apps.sync.urls')),
]