import os
from .using_elasticsearch import *

SHARED_INSTALLED_APPS = [
    'django_cleanup.apps.CleanupConfig'
]

if USING_ELASTICSEARCH:
    SHARED_INSTALLED_APPS.append('django_elasticsearch_dsl')