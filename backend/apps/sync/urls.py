from django.urls import path
from django.http import JsonResponse

def sync_status(request):
    """Заглушка для API синхронизации"""
    return JsonResponse({
        'status': 'ready',
        'last_sync': None,
        'message': 'Sync API ready'
    })

urlpatterns = [
    path('status/', sync_status, name='sync-status'),
]