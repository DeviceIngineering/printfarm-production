from django.urls import path
from django.views.decorators.csrf import csrf_exempt
from .emergency import warehouses, groups, status, products, stats, sync_start, settings_endpoint, settings_summary

urlpatterns = [
    path("sync/warehouses/", warehouses, name="warehouses"),
    path("sync/product-groups/", groups, name="product-groups"),
    path("sync/status/", status, name="sync-status"),
    path("sync/start/", csrf_exempt(sync_start), name="sync-start"),
    path("products/", products, name="products"),
    path("products/stats/", stats, name="products-stats"),
    path("settings/", settings_endpoint, name="settings"),
    path("settings/summary/", settings_summary, name="settings-summary"),
]