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
    PrinterStatsView,
    # Webhook Testing Views
    WebhookEventsListView,
    WebhookStatsView,
    WebhookTestTriggerView,
    WebhookClearOldEventsView,
    # Timeline Views
    TimelineJobsView
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

    # Webhook Testing endpoints (с аутентификацией)
    path('webhook/events/', WebhookEventsListView.as_view(), name='webhook-events'),
    path('webhook/stats/', WebhookStatsView.as_view(), name='webhook-stats'),
    path('webhook/test-trigger/', WebhookTestTriggerView.as_view(), name='webhook-test-trigger'),
    path('webhook/events/clear/', WebhookClearOldEventsView.as_view(), name='webhook-clear-events'),

    # Printer endpoints
    path('printers/sync/', PrinterSyncView.as_view(), name='printer-sync'),
    path('printers/', PrinterSnapshotsView.as_view(), name='printer-snapshots'),
    path('printers/stats/', PrinterStatsView.as_view(), name='printer-stats'),

    # Timeline endpoints
    path('timeline-jobs/', TimelineJobsView.as_view(), name='timeline-jobs'),

    # REST API endpoints (с аутентификацией)
    path('', include(router.urls)),
]
