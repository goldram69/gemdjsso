# your_project/settings/production.py

from .base import *
# No need to re-initialize env or call read_env() here.
# base.py handles loading the .env file based on DJANGO_SETTINGS_MODULE.

# Override base settings for production
DEBUG = False # Explicitly set DEBUG to False for production

# ALLOWED_HOSTS must be explicitly set in production .env
# This will be read from .env.production by base.py
# ALLOWED_HOSTS = env.list('ALLOWED_HOSTS')

# Database URL for production
# This will be read from .env.production by base.py
# DATABASES = {'default': env.db('DATABASE_URL')}

# Email settings for production SMTP service
# These will be read from .env.production by base.py
# EMAIL_BACKEND = env('EMAIL_BACKEND')
# EMAIL_HOST = env('EMAIL_HOST')
# EMAIL_PORT = env('EMAIL_PORT')
# EMAIL_USE_TLS = env('EMAIL_USE_TLS')
# EMAIL_USE_SSL = env('EMAIL_USE_SSL')
# EMAIL_HOST_USER = env('EMAIL_HOST_USER')
# EMAIL_HOST_PASSWORD = env('EMAIL_HOST_PASSWORD')
# DEFAULT_FROM_EMAIL = env('DEFAULT_FROM_EMAIL')

# Discourse Integration Settings for Production
# These will be read from .env.production by base.py
# DISCOURSE_SSO_SECRET = env('DISCOURSE_SSO_SECRET')
# DISCOURSE_BASE_URL = env('DISCOURSE_BASE_URL')
# DISCOURSE_API_KEY = env('DISCOURSE_API_KEY')
# DISCOURSE_API_USERNAME = env('DISCOURSE_API_USERNAME')
# DISCOURSE_SSO_CALLBACK_URL = env('DISCOURSE_SSO_CALLBACK_URL') # Should match your production external URL

# --- Production Security Settings ---
# Configure these appropriately for your production environment
# SECURE_SSL_REDIRECT = env.bool('SECURE_SSL_REDIRECT', default=True)
# SESSION_COOKIE_SECURE = env.bool('SESSION_COOKIE_SECURE', default=True)
# CSRF_COOKIE_SECURE = env.bool('CSRF_COOKIE_SECURE', default=True)
# SECURE_HSTS_SECONDS = env.int('SECURE_HSTS_SECONDS', default=31536000) # 1 year
# SECURE_HSTS_INCLUDE_SUBDOMAINS = env.bool('SECURE_HSTS_INCLUDE_SUBDOMAINS', default=True)
# SECURE_HSTS_PRELOAD = env.bool('SECURE_HSTS_PRELOAD', default=False) # Be cautious with HSTS preload
# SECURE_REFERRER_POLICY = env('SECURE_REFERRER_POLICY', default='same-origin')
# SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https') # If behind a proxy like Nginx

# Logging configuration for production
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
        # Add file handlers, Sentry handlers, etc. for production
        # 'file': {
        #     'class': 'logging.FileHandler',
        #     'filename': '/var/log/django/debug.log',
        #     'formatter': 'verbose',
        # },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
        'discourse_integration': { # Logger for your app
            'handlers': ['console'],
            'level': 'INFO', # Set to DEBUG for more verbose logging
            'propagate': False,
        },
        # Add loggers for other apps
    },
}
