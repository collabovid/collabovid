from django.http import HttpResponseNotFound
from django.shortcuts import render, redirect
from tasks.models import Task
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from datetime import timedelta
from django.utils import timezone
from tasks.launcher.task_launcher import get_task_launcher

from tasks.load import AVAILABLE_TASKS, get_task_by_id


@staff_member_required
def tasks(request):
    tasks = Task.objects.all().order_by('-started_at')
    return render(request, 'dashboard/tasks/task_overview.html', {'tasks': tasks})


@staff_member_required
def task_detail(request, id):
    task = Task.objects.get(pk=id)
    return render(request, 'dashboard/tasks/task_detail.html', {'task': task})


@staff_member_required
def select_task(request):
    if request.method == 'GET':
        return render(request, 'dashboard/tasks/task_select.html', {'services_with_tasks': AVAILABLE_TASKS})

    return HttpResponseNotFound()


@staff_member_required
def create_task(request, task_id):
    service, task_definition = get_task_by_id(task_id)

    if service and task_definition:
        if request.method == 'GET':
            return render(request, 'dashboard/tasks/task_create.html',
                          {'task_id': task_id, 'definition': task_definition})
        elif request.method == 'POST':

            task_launcher = get_task_launcher()

            task_config = {
                'service': service,
                'parameters': [],
                'started_by': request.user.username
            }

            for parameter in task_definition['parameters']:
                if parameter['is_primitive']:
                    task_config['parameters'].append(
                        {
                            'name': parameter['name'],
                            'type': parameter['type'],
                            'value': request.POST.get(parameter['name'], parameter['default'])
                        }
                    )

            task_launcher.launch_task(name=task_id, config=task_config, block=False)
            messages.add_message(request, messages.SUCCESS, 'Task started.')
            return redirect('tasks')

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
