"""
Celery configuration for PrintFarm production system.
"""
import os
from celery import Celery
from django.conf import settings

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

app = Celery('printfarm')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django apps.
app.autodiscover_tasks()

# Celery beat schedule for automatic sync
app.conf.beat_schedule = {
    'daily-sync': {
        'task': 'apps.sync.tasks.scheduled_sync',
        'schedule': 60.0 * 60.0 * 24.0,  # 24 hours
        'options': {'expires': 60.0 * 60.0 * 23.0}  # expire after 23 hours
    },
    'simpleprint-sync-30min': {
        'task': 'simpleprint.scheduled_sync',
        'schedule': 60.0 * 30.0,  # 30 minutes
        'options': {'expires': 60.0 * 25.0}  # expire after 25 minutes
    },
}

app.conf.timezone = settings.TIME_ZONE

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')