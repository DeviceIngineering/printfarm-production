from django.urls import path
from .views import (
    health_check, health_detailed, run_algorithm_regression_test,
    monitoring_dashboard, webhook_alert
)

urlpatterns = [
    path('health/', health_check, name='health-check'),
    path('health/detailed/', health_detailed, name='health-detailed'),
    path('algorithm/regression-test/', run_algorithm_regression_test, name='algorithm-regression-test'),
    path('dashboard/', monitoring_dashboard, name='monitoring-dashboard'),
    path('webhook/alert/', webhook_alert, name='webhook-alert'),
]