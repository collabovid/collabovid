from .models import Task
from .definitions import AVAILABLE_TASKS
import random


def generate_tasks():
    tasks = []
    for i in range(10):
        name = random.choice(list(AVAILABLE_TASKS.items()))[0]
        status = random.choice(Task.STATUS_CHOICES)[0]
        t = Task(name=name, status=status)
        tasks.append(t)
    return tasks
