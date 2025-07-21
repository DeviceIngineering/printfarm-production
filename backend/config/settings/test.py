from .base import *

# Test settings
DEBUG = False
TESTING = True

# Use in-memory SQLite for tests
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
        'TEST': {
            'NAME': ':memory:',
        },
    }
}

# Disable Celery for tests
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True
CELERY_BROKER_URL = 'memory://'
CELERY_RESULT_BACKEND = 'cache+memory://'

# Disable Redis caching for tests
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
    }
}

# Disable external API calls in tests
MOYSKLAD_TOKEN = 'test-token'
MOYSKLAD_BASE_URL = 'https://api.moysklad.ru/api/remap/1.2'

# Simplified logging for tests
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'null': {
            'class': 'logging.NullHandler',
        },
    },
    'root': {
        'handlers': ['null'],
    },
    'loggers': {
        'apps': {
            'handlers': ['null'],
            'level': 'ERROR',
            'propagate': False,
        },
        'django': {
            'handlers': ['null'],
            'level': 'ERROR',
            'propagate': False,
        },
    },
}

# Disable migrations for faster tests
class DisableMigrations:
    def __contains__(self, item):
        return True
    
    def __getitem__(self, item):
        return None

# Disable authentication for tests  
REST_FRAMEWORK = {
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.AllowAny',
    ],
    'DEFAULT_AUTHENTICATION_CLASSES': [],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 100,
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
    ],
}

# Speed up password hashing for tests
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.MD5PasswordHasher',
]

# Test email backend
EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'

# Disable static file collection in tests
STATIC_ROOT = None