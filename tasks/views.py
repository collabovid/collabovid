from django.shortcuts import render
from .models import Task


# Create your views here.


def tasks(request):
    tasks = Task.objects.all()
    return render(request, 'tasks/task_overview.html', {'tasks': tasks})


def task_detail(request, id):
    task = Task.objects.get(pk=id)
    with open(task.log_file, 'r') as f:
        log = f.read()
    return render(request, 'tasks/task_detail.html', {'task': task, 'log': log})
