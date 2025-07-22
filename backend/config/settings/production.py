from .base import *

DEBUG = False

# CORS settings for production
CORS_ALLOW_ALL_ORIGINS = True  # Временно разрешить все origins для отладки
CORS_ALLOW_CREDENTIALS = True

# Дополнительные CORS заголовки
CORS_ALLOWED_HEADERS = [
    'accept',
    'accept-encoding',
    'authorization',
    'content-type',
    'dnt',
    'origin',
    'user-agent',
    'x-csrftoken',
    'x-requested-with',
]

CORS_ALLOWED_METHODS = [
    'DELETE',
    'GET',
    'OPTIONS',
    'PATCH',
    'POST',
    'PUT',
]

# Security settings for production - временно смягчены для отладки
SECURE_SSL_REDIRECT = False  # Отключено для HTTP доступа
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'SAMEORIGIN'  # Смягчено с 'DENY'

# Session security - временно смягчено
SESSION_COOKIE_SECURE = False  # Для HTTP доступа
CSRF_COOKIE_SECURE = False     # Для HTTP доступа
SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_HTTPONLY = False   # Смягчено для AJAX запросов

# HSTS - временно отключено
SECURE_HSTS_SECONDS = 0  # Отключено
SECURE_HSTS_INCLUDE_SUBDOMAINS = False
SECURE_HSTS_PRELOAD = False