from .base import *

DEBUG = True

# For server development, allow all hosts
ALLOWED_HOSTS = ['*']

# Отключаем аутентификацию для server development
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

# Keep PostgreSQL settings from base.py for server deployment

# Additional CORS origins for server development
CORS_ALLOWED_ORIGINS += [
    "http://frontend:3000",
    "http://localhost:3000",
    "http://kemomail3.keenetic.pro:3000",
]

# More permissive CORS for development
CORS_ALLOW_ALL_ORIGINS = True

# CSRF trusted origins
CSRF_TRUSTED_ORIGINS = [
    "http://localhost:3000",
    "http://kemomail3.keenetic.pro:3000",
]

# Отключаем CSRF для development
CSRF_COOKIE_SECURE = False
SESSION_COOKIE_SECURE = False
SECURE_SSL_REDIRECT = False