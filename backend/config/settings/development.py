from .base import *

DEBUG = True

# For development, allow all hosts
ALLOWED_HOSTS = ['*']

# Use SQLite for development
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
]

# More permissive CORS for development
CORS_ALLOW_ALL_ORIGINS = True

# Django Extensions already in base.py

# Development-specific logging
LOGGING['handlers']['console']['level'] = 'DEBUG'
LOGGING['loggers']['apps']['level'] = 'DEBUG'