from .base_settings import *

SECRET_KEY = '$bi4%atjzaoj720b0d58&y6&=vfu)0*-!h4xwpgzfsrkvlt))y'
ALLOWED_HOSTS = []
DEBUG = True

INSTALLED_APPS.append('classification.apps.ClassificationConfig')

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    }
}
