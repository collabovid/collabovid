import os

RESOURCES_DIR = os.path.join(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                                               '../../'), 'resources')
MODELS_BASE_DIR = os.path.join(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                                               '../../'), 'models')
GEONAMES_DB_PATH = os.path.join(RESOURCES_DIR, 'geonames/geonames.sqlite3')