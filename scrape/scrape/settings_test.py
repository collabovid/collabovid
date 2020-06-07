from scrape.settings_prod import *

ALLOW_IMAGE_SCRAPING = True
DEBUG = True

RESOURCES_DIR = os.getenv('SCRAPE_DOWNLOADS_BASE_DIR', None)
