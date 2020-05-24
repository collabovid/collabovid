from scrape.settings_base import *
from collabovid_settings.postgres_settings import *
from collabovid_settings.tasks_settings import *
from collabovid_settings.service_settings import *
from collabovid_settings.aws_settings import *

DEBUG = False

if int(os.getenv('ALLOW_IMAGE_SCRAPING', 0)) > 0:
    ALLOW_IMAGE_SCRAPING = True
else:
    ALLOW_IMAGE_SCRAPING = False

DB_EXPORT_STORE_LOCALLY = False
DB_EXPORT_LOCAL_DIR = "tmp"

