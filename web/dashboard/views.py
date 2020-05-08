from django.http import HttpResponseNotFound
from django.shortcuts import render, redirect
from tasks.models import Task
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from datetime import timedelta
from django.utils import timezone
from dashboard.tasks.tasks import get_available_tasks
from dashboard.tasks.task_launcher import KubeTaskLauncher


@staff_member_required
def tasks(request):
    tasks = Task.objects.all().order_by('-started_at')
    return render(request, 'dashboard/tasks/task_overview.html', {'tasks': tasks})


@staff_member_required
def task_detail(request, id):
    task = Task.objects.get(pk=id)
    return render(request, 'dashboard/tasks/task_detail.html', {'task': task})


@staff_member_required
def create_task(request):
    available_tasks = get_available_tasks()
    if request.method == 'GET':
        tasks = []
        for name, config in available_tasks.items():
            tasks.append({
                'name': name,
                'description': ''
            })
        return render(request, 'dashboard/tasks/task_create.html', {'tasks': tasks})
    elif request.method == 'POST':
        task_name = request.POST.get('task')
        if task_name in available_tasks.keys():
            task_launcher = KubeTaskLauncher()
            task_config = available_tasks[task_name]
            task_launcher.launch_task(name=task_name, config=task_config)
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