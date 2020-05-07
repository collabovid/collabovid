from .settings_base import *
from collabovid_settings.development.service_settings import *
from collabovid_settings.development.sqlite_settings import *

ALLOWED_HOSTS += [SEARCH_SERVICE_HOST]

SECRET_KEY = '7_%)-$#43s2hk6e6)ip)4+*3d6vz&73%zqos7un9qkz$2pt@h*'

DEBUG = True