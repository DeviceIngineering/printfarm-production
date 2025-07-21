from .base import *

DEBUG = True

# For development, allow all hosts
ALLOWED_HOSTS = ['*']

# Отключаем аутентификацию для development
REST_FRAMEWORK = {
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 100,
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.AllowAny',  # Разрешаем всем
    ],
    'DEFAULT_AUTHENTICATION_CLASSES': [
        # Отключаем аутентификацию
    ],
}

# Use PostgreSQL for server development (keep database settings from base.py)

# Additional CORS origins for development
CORS_ALLOWED_ORIGINS += [
    "http://frontend:3000",
    "http://localhost:3000",
]

# More permissive CORS for development
CORS_ALLOW_ALL_ORIGINS = True

# Django Extensions already in base.py

# Development-specific logging
LOGGING['handlers']['console']['level'] = 'DEBUG'
LOGGING['loggers']['apps']['level'] = 'DEBUG'