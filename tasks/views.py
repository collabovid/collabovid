from django.shortcuts import render
from .dummy_tasks import generate_tasks


# Create your views here.


def tasks(request):
    tasks = generate_tasks()
    return render(request, 'tasks/task_overview.html', {'tasks': tasks})
