from django.urls import path
from django.http import JsonResponse

def products_list(request):
    """Заглушка для API товаров"""
    return JsonResponse({
        'count': 0,
        'results': [],
        'message': 'Products API ready'
    })

urlpatterns = [
    path('', products_list, name='products-list'),
]