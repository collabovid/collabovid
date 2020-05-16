from django.urls import path, include
from src.tasks import *

urlpatterns = [
    path('', include('api.urls')),
    path('tasks/', include('tasks.urls'))
]
