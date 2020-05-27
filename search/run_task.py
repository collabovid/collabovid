"""
Runs a given task or returns a list of available tasks for this service.
"""
import os
import django

if __name__ == "__main__":
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'search.settings_dev')
    django.setup()

    from src.tasks import *
    from tasks.task_runner import CommandLineTaskRunner

    CommandLineTaskRunner.run_task()


