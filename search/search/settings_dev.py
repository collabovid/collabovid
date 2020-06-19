from .settings_base import *
from collabovid_settings.development.service_settings import *
from collabovid_settings.development.database_settings import *
from collabovid_settings.development.tasks_settings import *
from collabovid_settings.development.volumes_settings import *

os.environ['NLTK_DATA'] = os.path.join(RESOURCES_DIR, 'nltk_data')

ALLOWED_HOSTS += [SEARCH_SERVICE_HOST]
SECRET_KEY = '7_%)-$#43s2hk6e6)ip)4+*3d6vz&73%zqos7un9qkz$2pt@h*'
DEBUG = True

PAPER_MATRIX_BASE_DIR = os.path.join(MODELS_BASE_DIR, 'paper_matrix')
PUSH_PAPER_MATRIX = False
