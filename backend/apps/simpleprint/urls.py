"""
URL маршруты для SimplePrint app
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    SimplePrintWebhookView,
    SimplePrintFileViewSet,
    SimplePrintFolderViewSet,
    SimplePrintSyncViewSet,
    PrinterSyncView,
    PrinterSnapshotsView,
    PrinterStatsView
)

app_name = 'simpleprint'

# REST API Router
router = DefaultRouter()
router.register(r'files', SimplePrintFileViewSet, basename='file')
router.register(r'folders', SimplePrintFolderViewSet, basename='folder')
router.register(r'sync', SimplePrintSyncViewSet, basename='sync')

urlpatterns = [
    # Webhook endpoint (без аутентификации)
    path('webhook/', SimplePrintWebhookView.as_view(), name='webhook'),

    # Printer endpoints
    path('printers/sync/', PrinterSyncView.as_view(), name='printer-sync'),
    path('printers/', PrinterSnapshotsView.as_view(), name='printer-snapshots'),
    path('printers/stats/', PrinterStatsView.as_view(), name='printer-stats'),

    # REST API endpoints (с аутентификацией)
    path('', include(router.urls)),
]
