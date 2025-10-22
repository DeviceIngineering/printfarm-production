"""
URL маршруты для SimplePrint app
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    SimplePrintWebhookView,
    SimplePrintFileViewSet,
    SimplePrintFolderViewSet,
    SimplePrintSyncViewSet
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

    # REST API endpoints (с аутентификацией)
    path('', include(router.urls)),
]
