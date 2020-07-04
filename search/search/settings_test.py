from .settings_prod import *
from collabovid_settings.tasks_settings import *

ALLOWED_HOSTS += ['localhost']
DEBUG = True

PUSH_PAPER_MATRIX = int(os.getenv("PUSH_PAPER_MATRIX", "1")) > 0
