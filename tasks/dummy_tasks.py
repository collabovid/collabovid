from .models import Task
from .definitions import AVAILABLE_TASKS
import random
import django.utils.timezone as timezone

tasks = []
for i in range(10):
    start = timezone.now() - timezone.timedelta(seconds=random.randint(1, 2000))
    end = start + timezone.timedelta(seconds=random.randint(1, 2000))
    name = random.choice(list(AVAILABLE_TASKS.items()))[0]
    status = random.choice(Task.STATUS_CHOICES)[0]
    t = Task(pk=i, name=name, status=status, started_at=start, ended_at=end)
    tasks.append(t)


def generate_tasks():
    return tasks
