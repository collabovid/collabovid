from django.urls import path, include
from .views import *

urlpatterns = [
    path('', tasks, name='tasks'),
    path('detail/<int:id>', task_detail, name='task_detail')
]