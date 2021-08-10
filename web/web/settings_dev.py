from .settings_base import *
from collabovid_settings.development.database_settings import *
from collabovid_settings.development.service_settings import *
from collabovid_settings.development.tasks_settings import *
from collabovid_settings.development.aws_settings import *
from collabovid_settings.development.export_settings import *
from collabovid_settings.development.volumes_settings import *
from collabovid_settings.development.elasticsearch_settings import *

SECRET_KEY = '$bi4%atjzaoj720b0d58&y6&=vfu)0*-!h4xwpgzfsrkvlt))y'
ALLOWED_HOSTS += ['*']
DEBUG = True

SAVE_SEARCH_QUERIES = False
STATISTICS_URL = os.getenv("STATISTICS_URL", "https://collabovid.s3.eu-central-1.amazonaws.com/statistics/statistics.json")

if "NO_CACHE" in os.environ and os.getenv("NO_CACHE"):
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
        }
    }
else:
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
            'LOCATION': 'unique-snowflake',
        }
    }