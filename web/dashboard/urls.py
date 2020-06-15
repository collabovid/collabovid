from django.urls import path, include
from django.shortcuts import redirect
from .views import *

urlpatterns = [
    path('', lambda request: redirect('tasks', permanent=False), name='dashboard'),
    path('tasks', tasks, name='tasks'),
    path('tasks/detail/<int:id>', task_detail, name='task_detail'),
    path('tasks/create/', select_task, name='task_select'),
    path('tasks/create/<str:task_id>', create_task, name='task_create'),
    path('tasks/delete/', delete_task, name='task_delete'),
    path('tasks/delete-all/', delete_all_finished, name='task_delete_all'),
    #path('data-sanitizing', data_sanitizing, name='data-sanitizing'),
    path('data-import', data_import, name='data_import'),
    path('data-import/delete-archive/<path:archive_path>', delete_archive, name='delete_archive'),
    path('sanitizing/location', location_sanitizing, name='location_sanitizing'),
]
