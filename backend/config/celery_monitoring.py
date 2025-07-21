"""
Celery beat schedule for monitoring tasks.
"""
from celery.schedules import crontab

CELERYBEAT_SCHEDULE = {
    # System health collection every 5 minutes
    'collect-system-health': {
        'task': 'apps.monitoring.tasks.collect_system_health',
        'schedule': crontab(minute='*/5'),
    },
    
    # Algorithm regression tests every hour
    'algorithm-regression-tests': {
        'task': 'apps.monitoring.tasks.run_algorithm_regression_tests',
        'schedule': crontab(minute=0),
    },
    
    # Performance trend analysis every 4 hours
    'check-performance-trends': {
        'task': 'apps.monitoring.tasks.check_algorithm_performance_trends',
        'schedule': crontab(minute=0, hour='*/4'),
    },
    
    # Daily monitoring report at 9 AM
    'daily-monitoring-report': {
        'task': 'apps.monitoring.tasks.send_daily_monitoring_report',
        'schedule': crontab(minute=0, hour=9),
    },
    
    # Cleanup old data daily at 2 AM
    'cleanup-monitoring-data': {
        'task': 'apps.monitoring.tasks.cleanup_old_monitoring_data',
        'schedule': crontab(minute=0, hour=2),
    },
}