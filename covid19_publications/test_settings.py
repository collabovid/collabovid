from .prod_settings import *

ALLOWED_HOSTS = [os.environ['ALLOWED_TEST_HOST']]

ALLOW_IMAGE_SCRAPING = False
