import os
from collabovid_settings.installed_apps import SHARED_INSTALLED_APPS
from collabovid_settings.using_elasticsearch import USING_ELASTICSEARCH

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

SECRET_KEY = 'test'

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'data',
    'tasks'
]
INSTALLED_APPS += SHARED_INSTALLED_APPS

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_L10N = True
USE_TZ = True

UPDATE_VECTORIZER = True

