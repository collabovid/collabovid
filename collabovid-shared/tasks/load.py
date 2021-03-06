import json
from os.path import dirname, join, realpath

"""
The tasks.json is part of the collabovid-shared project and contains all tasks from all services.
The variables in this module are used for calling these tasks.
"""
TASKS_FILE_NAME = join(dirname(realpath(__file__)), 'resources/tasks.json')

with open(TASKS_FILE_NAME, 'r') as f:
    AVAILABLE_TASKS = json.load(f)


def get_task_by_id(requested_id):
    for service, tasks_for_service in AVAILABLE_TASKS.items():
        for task_id, definition in tasks_for_service.items():
            if task_id == requested_id:
                return service, definition

    return None, None
