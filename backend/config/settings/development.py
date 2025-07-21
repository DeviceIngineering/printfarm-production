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

# Use SQLite for local development
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Additional CORS origins for development
CORS_ALLOWED_ORIGINS += [
    "http://frontend:3000",
    "http://localhost:3000",
    "file://",  # For local HTML files
]

# More permissive CORS for development
CORS_ALLOW_ALL_ORIGINS = True
CORS_ALLOW_CREDENTIALS = True

# Django Extensions already in base.py

# Development-specific logging
LOGGING['handlers']['console']['level'] = 'DEBUG'
LOGGING['loggers']['apps']['level'] = 'DEBUG'