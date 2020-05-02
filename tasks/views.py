from django.http import HttpResponseNotFound
from django.shortcuts import render, redirect
from .models import Task
from .definitions import AVAILABLE_TASKS
from tasks.task_runner import TaskRunner
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from datetime import timedelta
from django.utils import timezone


@staff_member_required
def tasks(request):
    tasks = Task.objects.all().order_by('-started_at')
    return render(request, 'tasks/task_overview.html', {'tasks': tasks})


@staff_member_required
def task_detail(request, id):
    task = Task.objects.get(pk=id)
    return render(request, 'tasks/task_detail.html', {'task': task})


@staff_member_required
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
            TaskRunner.run_task_async(cls, started_by=request.user.username)
            messages.add_message(request, messages.SUCCESS, 'Task started.')
            return redirect('tasks')
        else:
            messages.add_message(request, messages.ERROR, 'Unknown Task name')
            return redirect('task_create')
    return HttpResponseNotFound()


@staff_member_required
def delete_task(request):
    if request.method == 'POST':
        id = request.POST.get('id')
        print(id)
        query = Task.objects.filter(pk=id)
        if query.count() > 0:
            query.delete()
            messages.add_message(request, messages.SUCCESS, 'Deleted Task.')
        else:
            messages.add_message(request, messages.ERROR, 'Failed to delete Task: Unknown Task.')
        return redirect('tasks')
    return HttpResponseNotFound()


@staff_member_required
def delete_all_finished(request):
    if request.method == 'POST':
        days = 1
        date_limit = timezone.now() - timedelta(days=days)
        query = Task.objects.filter(status=Task.STATUS_FINISHED, ended_at__lte=date_limit)
        if query.count() > 0:
            query.delete()
            messages.add_message(request, messages.SUCCESS, 'Deleted All Finished Tasks.')
        else:
            messages.add_message(request, messages.WARNING, 'No Tasks to delete.')
        return redirect('tasks')
    return HttpResponseNotFound()
