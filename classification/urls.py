from django.urls import path, include
from .views import *

urlpatterns = [
    path('', classify_index, name='classify'),
]
