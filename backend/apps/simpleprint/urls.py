"""
URL маршруты для SimplePrint app
"""

from django.urls import path
from .views import SimplePrintWebhookView

app_name = 'simpleprint'

urlpatterns = [
    path('webhook/', SimplePrintWebhookView.as_view(), name='webhook'),
]
