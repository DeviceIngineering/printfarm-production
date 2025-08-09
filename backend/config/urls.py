"""
URL configuration for PrintFarm project.
"""
from django.contrib import admin
from django.urls import path, include
from django.http import JsonResponse
from django.conf import settings
from django.conf.urls.static import static


def health_check(request):
    """Health check endpoint"""
    return JsonResponse({
        'status': 'healthy',
        'service': 'PrintFarm Backend',
        'version': '1.0.0'
    })


urlpatterns = [
    path('admin/', admin.site.urls),
    path('health/', health_check, name='health'),
    path('api/v1/', include('apps.api.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)