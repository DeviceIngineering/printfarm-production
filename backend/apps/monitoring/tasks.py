"""
Celery tasks for monitoring system.
"""
from celery import shared_task
from django.utils import timezone
from .services import AlgorithmMonitor, SystemHealthMonitor
from .models import AlgorithmAlert, SystemHealth
import logging

logger = logging.getLogger('apps.monitoring')


@shared_task
def collect_system_health():
    """
    Collect system health metrics.
    Run every 5 minutes.
    """
    try:
        health_monitor = SystemHealthMonitor()
        health = health_monitor.collect_health_metrics()
        
        logger.info(f"Health collected: {health.health_score}% ({'healthy' if health.is_healthy else 'unhealthy'})")
        return {
            'success': True,
            'health_score': float(health.health_score),
            'is_healthy': health.is_healthy
        }
    except Exception as e:
        logger.error(f"Failed to collect health metrics: {e}")
        return {
            'success': False,
            'error': str(e)
        }


@shared_task
def run_algorithm_regression_tests():
    """
    Run algorithm regression tests.
    Run every hour.
    """
    try:
        monitor = AlgorithmMonitor()
        results = monitor.run_regression_tests()
        
        logger.info(f"Regression tests: {results['passed_tests']}/{results['total_tests']} passed")
        return results
    except Exception as e:
        logger.error(f"Failed to run regression tests: {e}")
        return {
            'success': False,
            'error': str(e)
        }


@shared_task
def cleanup_old_monitoring_data():
    """
    Clean up old monitoring data.
    Run daily.
    """
    try:
        # Keep health data for 7 days
        cutoff_date = timezone.now() - timezone.timedelta(days=7)
        deleted_health = SystemHealth.objects.filter(timestamp__lt=cutoff_date).delete()
        
        # Keep resolved alerts for 30 days
        alert_cutoff = timezone.now() - timezone.timedelta(days=30)
        deleted_alerts = AlgorithmAlert.objects.filter(
            status='resolved',
            resolved_at__lt=alert_cutoff
        ).delete()
        
        logger.info(f"Cleaned up {deleted_health[0]} health records and {deleted_alerts[0]} alerts")
        return {
            'success': True,
            'deleted_health_records': deleted_health[0],
            'deleted_alerts': deleted_alerts[0]
        }
    except Exception as e:
        logger.error(f"Failed to cleanup monitoring data: {e}")
        return {
            'success': False,
            'error': str(e)
        }


@shared_task
def send_daily_monitoring_report():
    """
    Send daily monitoring report.
    Run daily at 9 AM.
    """
    try:
        # Get yesterday's data
        yesterday = timezone.now() - timezone.timedelta(days=1)
        start_of_yesterday = yesterday.replace(hour=0, minute=0, second=0, microsecond=0)
        end_of_yesterday = start_of_yesterday + timezone.timedelta(days=1)
        
        # Health metrics
        health_records = SystemHealth.objects.filter(
            timestamp__gte=start_of_yesterday,
            timestamp__lt=end_of_yesterday
        )
        
        avg_health_score = sum(h.health_score for h in health_records) / max(len(health_records), 1)
        unhealthy_periods = health_records.filter(is_healthy=False).count()
        
        # Alerts
        alerts_yesterday = AlgorithmAlert.objects.filter(
            created_at__gte=start_of_yesterday,
            created_at__lt=end_of_yesterday
        )
        
        critical_alerts = alerts_yesterday.filter(severity='critical').count()
        total_alerts = alerts_yesterday.count()
        
        # Create summary
        report = {
            'date': yesterday.strftime('%Y-%m-%d'),
            'health': {
                'avg_score': float(avg_health_score),
                'unhealthy_periods': unhealthy_periods,
                'total_checks': len(health_records)
            },
            'alerts': {
                'total': total_alerts,
                'critical': critical_alerts,
                'high': alerts_yesterday.filter(severity='high').count(),
                'medium': alerts_yesterday.filter(severity='medium').count(),
            }
        }
        
        # Send report (implement actual sending logic)
        logger.info(f"Daily monitoring report: {report}")
        
        # TODO: Send email report or post to Slack
        
        return report
    except Exception as e:
        logger.error(f"Failed to send daily report: {e}")
        return {
            'success': False,
            'error': str(e)
        }


@shared_task
def check_algorithm_performance_trends():
    """
    Check for algorithm performance degradation trends.
    Run every 4 hours.
    """
    try:
        from apps.monitoring.models import AlgorithmExecution
        
        # Get executions from last 24 hours
        last_24h = timezone.now() - timezone.timedelta(hours=24)
        recent_executions = AlgorithmExecution.objects.filter(
            started_at__gte=last_24h,
            duration_seconds__isnull=False
        )
        
        if recent_executions.count() < 5:
            return {'message': 'Not enough data for trend analysis'}
        
        # Calculate average execution time for each type
        execution_types = recent_executions.values_list('execution_type', flat=True).distinct()
        
        alerts_created = 0
        for exec_type in execution_types:
            executions = recent_executions.filter(execution_type=exec_type)
            
            if executions.count() < 3:
                continue
            
            # Get recent vs older executions
            recent_half = executions[:executions.count()//2]
            older_half = executions[executions.count()//2:]
            
            recent_avg = sum(e.duration_seconds for e in recent_half) / len(recent_half)
            older_avg = sum(e.duration_seconds for e in older_half) / len(older_half)
            
            # Check for significant degradation (>50% slower)
            if recent_avg > older_avg * 1.5:
                monitor = AlgorithmMonitor()
                monitor._create_alert(
                    alert_type='performance',
                    severity='medium',
                    title=f"Performance Degradation Trend Detected: {exec_type}",
                    description=f"Algorithm execution time increased from {older_avg:.2f}s to {recent_avg:.2f}s",
                    details={
                        'execution_type': exec_type,
                        'old_average': float(older_avg),
                        'new_average': float(recent_avg),
                        'degradation_percent': float((recent_avg - older_avg) / older_avg * 100)
                    }
                )
                alerts_created += 1
        
        return {
            'success': True,
            'alerts_created': alerts_created,
            'execution_types_checked': list(execution_types)
        }
        
    except Exception as e:
        logger.error(f"Failed to check performance trends: {e}")
        return {
            'success': False,
            'error': str(e)
        }