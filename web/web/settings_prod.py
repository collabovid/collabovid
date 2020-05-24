from .settings_base import *
from collabovid_settings.postgres_settings import *
from collabovid_settings.service_settings import *
from collabovid_settings.tasks_settings import *
from collabovid_settings.aws_settings import *
from collabovid_settings.export_settings import *

DEBUG = False

INSTALLED_APPS.append('storages')

ALLOWED_HOSTS = ['www.collabovid.org', 'collabovid.org']

EXTRA_HOST = os.getenv('ALLOWED_TEST_HOST', '')

if len(EXTRA_HOST) > 0:
    ALLOWED_HOSTS.append(EXTRA_HOST)

SECRET_KEY = os.getenv('SECRET_KEY')

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


USING_ANALYTICS = True
