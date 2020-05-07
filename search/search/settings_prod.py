from .settings_base import *
from collabovid_settings.service_settings import *

ALLOWED_HOSTS += SEARCH_SERVICE_HOST

SECRET_KEY = os.getenv('SECRET_KEY', '7_%)-$#43s2hk6e6)ip)4+*9d6vz&73%zqos7un9qkz52pt@h*')