from django.urls import path

from .views import *

urlpatterns = [
    path('', data_sanitizing, name='data-sanitizing'),
]
