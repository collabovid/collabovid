from django.urls import path, include
from .views import *

urlpatterns = [
    path('', tasks, name='tasks'),
    path('detail/<int:id>', task_detail, name='task_detail'),
    path('create/', create_task, name='task_create'),
    path('delete/', delete_task, name='task_delete'),
    path('deleteAll/', delete_all_finished, name='task_delete_all')
]
