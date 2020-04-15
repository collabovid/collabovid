from django.http import HttpResponseNotFound
from django.shortcuts import render, redirect
from .models import Task
from .definitions import AVAILABLE_TASKS
from tasks.task_runner import TaskRunner
from django.contrib import messages


# Create your views here.


def tasks(request):
    tasks = Task.objects.all().order_by('-started_at')
    return render(request, 'tasks/task_overview.html', {'tasks': tasks})


def task_detail(request, id):
    task = Task.objects.get(pk=id)
    with open(task.log_file, 'r') as f:
        log = f.read()
    return render(request, 'tasks/task_detail.html', {'task': task, 'log': log})


def create_task(request):
    if request.method == 'GET':
        tasks = []
        for task in AVAILABLE_TASKS.values():
            name = task.task_name()
            description = task.description()
            tasks.append({
                'name': name,
                'description': description
            })
        return render(request, 'tasks/task_create.html', {'tasks': tasks})
    elif request.method == 'POST':
        task_name = request.POST.get('task')
        if task_name in AVAILABLE_TASKS:
            cls = AVAILABLE_TASKS[task_name]
            TaskRunner.run_task_async(cls)
            messages.add_message(request, messages.SUCCESS, 'Task started.')
            return redirect('tasks')
        else:
            messages.add_message(request, messages.ERROR, 'Unknown Task name')
            return redirect('task_create')
    return HttpResponseNotFound()
