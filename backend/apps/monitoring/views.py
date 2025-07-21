"""
Monitoring and health check views.
"""
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
import logging

from .services import AlgorithmMonitor, SystemHealthMonitor
from .models import AlgorithmAlert, SystemHealth, AlgorithmExecution

logger = logging.getLogger('apps.monitoring')


@api_view(['GET'])
@permission_classes([AllowAny])
def health_check(request):
    """
    Basic health check endpoint for load balancers and monitoring systems.
    Returns 200 OK if system is healthy, 503 if unhealthy.
    """
    try:
        # Get latest health record
        latest_health = SystemHealth.objects.first()
        
        if not latest_health:
            # No health data available, run quick check
            health_monitor = SystemHealthMonitor()
            latest_health = health_monitor.collect_health_metrics()
        
        # Check if health record is too old (more than 1 hour)
        if latest_health.timestamp < timezone.now() - timezone.timedelta(hours=1):
            health_monitor = SystemHealthMonitor()
            latest_health = health_monitor.collect_health_metrics()
        
        response_data = {
            'status': 'healthy' if latest_health.is_healthy else 'unhealthy',
            'timestamp': latest_health.timestamp.isoformat(),
            'health_score': float(latest_health.health_score),
            'checks': {
                'api': 'ok' if latest_health.api_response_time_ms < 1000 else 'slow',
                'database': 'ok' if latest_health.database_connection_time_ms < 100 else 'slow',
                'redis': 'ok' if latest_health.redis_response_time_ms < 50 else 'slow',
                'memory': 'ok' if latest_health.memory_usage_percent < 80 else 'high',
                'cpu': 'ok' if latest_health.cpu_usage_percent < 80 else 'high',
            }
        }
        
        if latest_health.is_healthy:
            return Response(response_data, status=status.HTTP_200_OK)
        else:
            return Response(response_data, status=status.HTTP_503_SERVICE_UNAVAILABLE)
            
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return Response({
            'status': 'error',
            'message': 'Health check failed',
            'timestamp': timezone.now().isoformat()
        }, status=status.HTTP_503_SERVICE_UNAVAILABLE)


@api_view(['GET'])
@permission_classes([AllowAny])
def health_detailed(request):
    """
    Detailed health check with full metrics.
    """
    try:
        # Get latest health record
        latest_health = SystemHealth.objects.first()
        
        if not latest_health:
            health_monitor = SystemHealthMonitor()
            latest_health = health_monitor.collect_health_metrics()
        
        # Get recent alerts
        recent_alerts = AlgorithmAlert.objects.filter(
            created_at__gte=timezone.now() - timezone.timedelta(hours=24),
            status__in=['open', 'acknowledged']
        ).order_by('-created_at')[:10]
        
        # Get recent algorithm executions
        recent_executions = AlgorithmExecution.objects.filter(
            started_at__gte=timezone.now() - timezone.timedelta(hours=24)
        ).order_by('-started_at')[:10]
        
        response_data = {
            'status': 'healthy' if latest_health.is_healthy else 'unhealthy',
            'health_score': float(latest_health.health_score),
            'timestamp': latest_health.timestamp.isoformat(),
            'metrics': {
                'api': {
                    'response_time_ms': float(latest_health.api_response_time_ms or 0),
                    'error_rate_percent': float(latest_health.api_error_rate),
                },
                'database': {
                    'connection_time_ms': float(latest_health.database_connection_time_ms or 0),
                    'avg_query_time_ms': float(latest_health.database_query_time_avg_ms or 0),
                    'active_connections': latest_health.database_connections_active,
                },
                'redis': {
                    'response_time_ms': float(latest_health.redis_response_time_ms or 0),
                    'memory_usage_mb': float(latest_health.redis_memory_usage_mb or 0),
                },
                'system': {
                    'memory_usage_percent': float(latest_health.memory_usage_percent or 0),
                    'cpu_usage_percent': float(latest_health.cpu_usage_percent or 0),
                    'disk_usage_percent': float(latest_health.disk_usage_percent or 0),
                },
                'application': {
                    'total_products': latest_health.total_products,
                    'products_needing_production': latest_health.products_needing_production,
                    'avg_calculation_time_ms': float(latest_health.avg_calculation_time_ms or 0),
                }
            },
            'alerts': {
                'total_active': recent_alerts.count(),
                'critical': recent_alerts.filter(severity='critical').count(),
                'high': recent_alerts.filter(severity='high').count(),
                'recent': [
                    {
                        'type': alert.alert_type,
                        'severity': alert.severity,
                        'title': alert.title,
                        'created_at': alert.created_at.isoformat()
                    }
                    for alert in recent_alerts[:5]
                ]
            },
            'algorithm': {
                'recent_executions': recent_executions.count(),
                'avg_execution_time_s': float(
                    sum(exec.duration_seconds or 0 for exec in recent_executions) / 
                    max(recent_executions.count(), 1)
                ),
                'errors_count': sum(exec.errors_encountered for exec in recent_executions),
            }
        }
        
        return Response(response_data, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Detailed health check failed: {e}")
        return Response({
            'status': 'error',
            'message': f'Detailed health check failed: {str(e)}',
            'timestamp': timezone.now().isoformat()
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([AllowAny])  # In production, add proper authentication
def run_algorithm_regression_test(request):
    """
    Endpoint to manually trigger algorithm regression tests.
    """
    try:
        monitor = AlgorithmMonitor()
        results = monitor.run_regression_tests()
        
        response_status = status.HTTP_200_OK if results['all_passed'] else status.HTTP_422_UNPROCESSABLE_ENTITY
        
        return Response({
            'success': results['all_passed'],
            'total_tests': results['total_tests'],
            'passed_tests': results['passed_tests'],
            'failed_tests': results['failed_tests'],
            'timestamp': timezone.now().isoformat(),
            'results': results['results']
        }, status=response_status)
        
    except Exception as e:
        logger.error(f"Algorithm regression test failed: {e}")
        return Response({
            'success': False,
            'error': str(e),
            'timestamp': timezone.now().isoformat()
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([AllowAny])
def monitoring_dashboard(request):
    """
    Get data for monitoring dashboard.
    """
    try:
        # Get health metrics for last 24 hours
        health_records = SystemHealth.objects.filter(
            timestamp__gte=timezone.now() - timezone.timedelta(hours=24)
        ).order_by('-timestamp')[:100]
        
        # Get algorithm executions for last 24 hours
        algorithm_executions = AlgorithmExecution.objects.filter(
            started_at__gte=timezone.now() - timezone.timedelta(hours=24)
        ).order_by('-started_at')[:50]
        
        # Get active alerts
        active_alerts = AlgorithmAlert.objects.filter(
            status__in=['open', 'acknowledged']
        ).order_by('-created_at')[:20]
        
        return Response({
            'health_trend': [
                {
                    'timestamp': record.timestamp.isoformat(),
                    'health_score': float(record.health_score),
                    'is_healthy': record.is_healthy,
                    'api_response_time': float(record.api_response_time_ms or 0),
                    'memory_usage': float(record.memory_usage_percent or 0),
                    'cpu_usage': float(record.cpu_usage_percent or 0),
                }
                for record in health_records
            ],
            'algorithm_performance': [
                {
                    'timestamp': exec.started_at.isoformat(),
                    'execution_type': exec.execution_type,
                    'duration_seconds': float(exec.duration_seconds or 0),
                    'products_processed': exec.products_processed,
                    'errors_count': exec.errors_encountered,
                }
                for exec in algorithm_executions
            ],
            'active_alerts': [
                {
                    'id': alert.id,
                    'type': alert.alert_type,
                    'severity': alert.severity,
                    'status': alert.status,
                    'title': alert.title,
                    'created_at': alert.created_at.isoformat(),
                }
                for alert in active_alerts
            ],
            'summary': {
                'total_health_records': health_records.count(),
                'avg_health_score': float(
                    sum(r.health_score for r in health_records) / max(health_records.count(), 1)
                ),
                'total_algorithm_executions': algorithm_executions.count(),
                'avg_execution_time': float(
                    sum(e.duration_seconds or 0 for e in algorithm_executions) / 
                    max(algorithm_executions.count(), 1)
                ),
                'total_active_alerts': active_alerts.count(),
                'critical_alerts': active_alerts.filter(severity='critical').count(),
            }
        })
        
    except Exception as e:
        logger.error(f"Dashboard data failed: {e}")
        return Response({
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@csrf_exempt
@require_http_methods(["POST"])
def webhook_alert(request):
    """
    Webhook endpoint for external monitoring systems to send alerts.
    """
    try:
        import json
        data = json.loads(request.body)
        
        # Create alert from webhook data
        alert = AlgorithmAlert.objects.create(
            alert_type='error',
            severity=data.get('severity', 'medium'),
            title=data.get('title', 'External Alert'),
            description=data.get('description', 'Alert received from external system'),
            details=data.get('details', {}),
        )
        
        logger.info(f"Created alert from webhook: {alert.title}")
        
        return JsonResponse({
            'success': True,
            'alert_id': alert.id
        })
        
    except Exception as e:
        logger.error(f"Webhook alert failed: {e}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)