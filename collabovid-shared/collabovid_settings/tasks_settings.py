import os

TASK_LOGGING_DB_FLUSH_SECONDS = int(os.getenv("TASK_LOGGING_DB_FLUSH_SECONDS", "1"))
TASK_LAUNCHER_LOCAL = False
SEARCH_MODELS_HOST_PATH=os.getenv('SEARCH_MODELS_HOST_PATH', '/.docker/collabovid-data/models')
