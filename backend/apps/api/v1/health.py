"""
Health check endpoints для мониторинга системы
"""
from django.http import JsonResponse
from django.db import connection
from django.core.cache import cache
from django.views.decorators.http import require_http_methods
from django.views.decorators.cache import never_cache
import redis
from decouple import config
import time
import logging

logger = logging.getLogger(__name__)


@require_http_methods(["GET"])
@never_cache
def health_check(request):
    """
    Простая проверка здоровья системы
    """
    return JsonResponse({
        'status': 'healthy',
        'version': config('APP_VERSION', default='4.1.8'),
        'environment': config('ENVIRONMENT', default='production')
    })


@require_http_methods(["GET"])
@never_cache
def health_check_detailed(request):
    """
    Детальная проверка всех компонентов системы
    """
    health_status = {
        'status': 'healthy',
        'version': config('APP_VERSION', default='4.1.8'),
        'environment': config('ENVIRONMENT', default='production'),
        'checks': {}
    }
    
    # Проверка базы данных
    try:
        start = time.time()
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
        db_time = round((time.time() - start) * 1000, 2)
        health_status['checks']['database'] = {
            'status': 'healthy',
            'response_time_ms': db_time
        }
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        health_status['checks']['database'] = {
            'status': 'unhealthy',
            'error': str(e)
        }
        health_status['status'] = 'degraded'
    
    # Проверка Redis
    try:
        start = time.time()
        redis_url = config('REDIS_URL', default='redis://localhost:6379/0')
        r = redis.from_url(redis_url)
        r.ping()
        redis_time = round((time.time() - start) * 1000, 2)
        health_status['checks']['redis'] = {
            'status': 'healthy',
            'response_time_ms': redis_time
        }
    except Exception as e:
        logger.error(f"Redis health check failed: {e}")
        health_status['checks']['redis'] = {
            'status': 'unhealthy',
            'error': str(e)
        }
        health_status['status'] = 'degraded'
    
    # Проверка кеша Django
    try:
        start = time.time()
        cache_key = 'health_check_test'
        cache.set(cache_key, 'test_value', 10)
        value = cache.get(cache_key)
        cache.delete(cache_key)
        cache_time = round((time.time() - start) * 1000, 2)
        health_status['checks']['cache'] = {
            'status': 'healthy' if value == 'test_value' else 'unhealthy',
            'response_time_ms': cache_time
        }
    except Exception as e:
        logger.error(f"Cache health check failed: {e}")
        health_status['checks']['cache'] = {
            'status': 'unhealthy',
            'error': str(e)
        }
        health_status['status'] = 'degraded'
    
    # Проверка файловой системы (static/media)
    try:
        import os
        from django.conf import settings
        
        static_exists = os.path.exists(settings.STATIC_ROOT)
        media_exists = os.path.exists(settings.MEDIA_ROOT)
        
        health_status['checks']['filesystem'] = {
            'status': 'healthy' if static_exists and media_exists else 'degraded',
            'static_dir': static_exists,
            'media_dir': media_exists
        }
    except Exception as e:
        logger.error(f"Filesystem health check failed: {e}")
        health_status['checks']['filesystem'] = {
            'status': 'unhealthy',
            'error': str(e)
        }
    
    # Определение HTTP статус кода
    if health_status['status'] == 'unhealthy':
        status_code = 503  # Service Unavailable
    elif health_status['status'] == 'degraded':
        status_code = 200  # OK but degraded
    else:
        status_code = 200  # OK
    
    return JsonResponse(health_status, status=status_code)


@require_http_methods(["GET"])
@never_cache  
def readiness_check(request):
    """
    Проверка готовности приложения принимать трафик
    Используется Kubernetes/Docker для определения готовности
    """
    try:
        # Проверяем подключение к БД
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        
        # Проверяем Redis
        redis_url = config('REDIS_URL', default='redis://localhost:6379/0')
        r = redis.from_url(redis_url)
        r.ping()
        
        return JsonResponse({
            'status': 'ready',
            'version': config('APP_VERSION', default='4.1.8')
        })
    except Exception as e:
        logger.error(f"Readiness check failed: {e}")
        return JsonResponse({
            'status': 'not_ready',
            'error': str(e)
        }, status=503)


@require_http_methods(["GET"])
@never_cache
def liveness_check(request):
    """
    Проверка жизнеспособности приложения
    Если эта проверка не проходит, контейнер должен быть перезапущен
    """
    return JsonResponse({
        'status': 'alive',
        'version': config('APP_VERSION', default='4.1.8')
    })