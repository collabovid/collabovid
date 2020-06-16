from scrape.settings_prod import *

ALLOW_IMAGE_SCRAPING = True
DEBUG = True

RESOURCES_DIR = os.getenv('RESOURCES_DIR', None)
