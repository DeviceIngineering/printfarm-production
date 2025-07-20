"""
Export views that support authentication via query parameters.
"""
from django.http import HttpResponse, JsonResponse
from django.views import View
from django.db import models
from rest_framework.authtoken.models import Token
from apps.products.models import Product
from .exporters import ProductsExporter


def authenticate_from_query(request):
    """
    Authenticate user from query parameter or header.
    """
    # First try header authentication
    auth_header = request.META.get('HTTP_AUTHORIZATION', '')
    if auth_header.startswith('Token '):
        token_key = auth_header.split(' ')[1]
    else:
        # Try query parameter
        token_key = request.GET.get('auth_token')
    
    if not token_key:
        return None
    
    try:
        token = Token.objects.get(key=token_key)
        return token.user
    except Token.DoesNotExist:
        return None


def export_products_excel(request):
    """
    Export products to Excel with query parameter authentication.
    """
    # Authenticate
    user = authenticate_from_query(request)
    if not user:
        return JsonResponse({'detail': 'Authentication required'}, status=401)
    
    # Apply filters from query params
    queryset = Product.objects.all()
    
    product_type = request.GET.get('product_type')
    if product_type:
        queryset = queryset.filter(product_type=product_type)
    
    production_needed = request.GET.get('production_needed')
    if production_needed == 'true':
        queryset = queryset.filter(production_needed__gt=0)
    
    min_priority = request.GET.get('min_priority')
    if min_priority:
        try:
            queryset = queryset.filter(production_priority__gte=int(min_priority))
        except ValueError:
            pass
    
    search = request.GET.get('search')
    if search:
        queryset = queryset.filter(
            models.Q(article__icontains=search) | 
            models.Q(name__icontains=search)
        )
    
    # Order by priority
    queryset = queryset.order_by('-production_priority', 'article')
    
    # Export
    exporter = ProductsExporter()
    return exporter.export_products(queryset)


def export_production_list_excel(request):
    """
    Export production list to Excel with query parameter authentication.
    """
    # Authenticate
    user = authenticate_from_query(request)
    if not user:
        return JsonResponse({'detail': 'Authentication required'}, status=401)
    
    # Get products that need production
    queryset = Product.objects.filter(production_needed__gt=0)
    queryset = queryset.order_by('-production_priority', 'article')
    
    # Export
    exporter = ProductsExporter()
    return exporter.export_products(queryset)