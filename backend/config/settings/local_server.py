from .base import *

DEBUG = False

# CORS settings for local server
CORS_ALLOW_ALL_ORIGINS = False
CORS_ALLOWED_ORIGINS = [
    "http://kemomail3.keenetic.pro:3000",
    "http://localhost:3000",
]

# Disable SSL redirect for local HTTP server
SECURE_SSL_REDIRECT = False

# Security settings appropriate for local network
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'

# Session security without HTTPS
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False
SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_HTTPONLY = False  # Allow CSRF token to be read by JS
SESSION_COOKIE_SAMESITE = 'Lax'
CSRF_COOKIE_SAMESITE = 'Lax'

# CSRF trusted origins
CSRF_TRUSTED_ORIGINS = [
    "http://kemomail3.keenetic.pro:3000",
]

# Allow host
ALLOWED_HOSTS = ['*']  # For local network, adjust as needed

# Static files
STATIC_ROOT = BASE_DIR / 'static'
MEDIA_ROOT = BASE_DIR / 'media'