from django.urls import path, include
from .views import *

urlpatterns = [
    path('start/<str:task_id>', start_task, name='start-task'),
]
