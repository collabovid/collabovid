from .settings_prod import *
from collabovid_settings.tasks_settings import *
from collabovid_settings.test.aws_settings import *

ALLOWED_HOSTS += ['localhost']
DEBUG = True
