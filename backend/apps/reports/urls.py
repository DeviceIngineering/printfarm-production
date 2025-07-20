from django.urls import path
from .views import reports_list
from .export_views import export_production_list_excel, export_products_excel

urlpatterns = [
    path('', reports_list, name='reports-list'),
    path('export/production-list/', export_production_list_excel, name='export-production-list'),
    path('export/production-list/<int:list_id>/', export_production_list_excel, name='export-production-list-by-id'),
    path('export/products/', export_products_excel, name='export-products'),
]