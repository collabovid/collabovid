from scrape.settings_base import *
from collabovid_settings.postgres_settings import *
from collabovid_settings.tasks_settings import *
from collabovid_settings.service_settings import *
from collabovid_settings.aws_settings import *
from collabovid_settings.export_settings import *

DEBUG = False

if int(os.getenv('ALLOW_IMAGE_SCRAPING', 0)) > 0:
    ALLOW_IMAGE_SCRAPING = True
else:
    ALLOW_IMAGE_SCRAPING = False

RESOURCES_DIR = os.getenv('RESOURCES_BASE_DIR', None)
