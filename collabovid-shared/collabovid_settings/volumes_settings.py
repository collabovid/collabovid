import os

MODELS_BASE_DIR = os.getenv('MODELS_BASE_DIR', None)
RESOURCES_DIR = os.getenv('RESOURCES_BASE_DIR', None)
GEONAMES_DB_PATH = os.path.join(RESOURCES_DIR, 'geonames/geonames.sqlite3')