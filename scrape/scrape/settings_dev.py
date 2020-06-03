from scrape.settings_base import *
from collabovid_settings.development.database_settings import *
from collabovid_settings.development.tasks_settings import *
from collabovid_settings.development.service_settings import *
from collabovid_settings.development.aws_settings import *
from collabovid_settings.development.export_settings import *

DEBUG = True
ALLOW_IMAGE_SCRAPING = False
RESOURCES_DIR = os.path.join(os.path.dirname(BASE_DIR), 'resources')

