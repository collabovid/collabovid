import json
from os.path import dirname, join, realpath

"""
The tasks.json is part of the collabovid-shared project and contains all tasks from all services.
The variables in this module are used for calling these tasks.
"""
TASKS_FILE_NAME = join(dirname(realpath(__file__)), 'resources/tasks.json')

with open(TASKS_FILE_NAME, 'r') as f:
    AVAILABLE_TASKS = json.load(f)
