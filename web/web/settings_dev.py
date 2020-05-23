from .settings_base import *
from collabovid_settings.development.sqlite_settings import *
from collabovid_settings.development.service_settings import *
from collabovid_settings.development.tasks_settings import *
from collabovid_settings.development.aws_settings import *

SECRET_KEY = '$bi4%atjzaoj720b0d58&y6&=vfu)0*-!h4xwpgzfsrkvlt))y'
ALLOWED_HOSTS += [WEB_SERVICE_HOST]
DEBUG = True
