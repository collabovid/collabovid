from .base_settings import *
from collabovid_settings.postgres_settings import *
from collabovid_settings.service_settings import *

INSTALLED_APPS.append('storages')

ALLOWED_HOSTS = ['www.collabovid.org', 'collabovid.org']

EXTRA_HOST = os.getenv('ALLOWED_TEST_HOST', '')

if len(EXTRA_HOST) > 0:
    ALLOWED_HOSTS.append(EXTRA_HOST)

SECRET_KEY = os.getenv('SECRET_KEY', 'test')


'''LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': '/var/log/app-logs/django.log',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file'],
            'level': 'DEBUG',
            'propagate': True,
        },
    },
}'''

CORS_REPLACE_HTTPS_REFERER = True
HOST_SCHEME = "https://"
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_PRELOAD = True
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_SECONDS = 1000000
SECURE_FRAME_DENY = True

SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True
X_FRAME_OPTIONS = 'DENY'
SECURE_REDIRECT_EXEMPT = [r'^system-health/$']

ALLOW_IMAGE_SCRAPING = True

if int(os.getenv('ALLOW_IMAGE_SCRAPING', 0)) > 0:
    ALLOW_IMAGE_SCRAPING = True
else:
    ALLOW_IMAGE_SCRAPING = False

USING_ANALYTICS = True
