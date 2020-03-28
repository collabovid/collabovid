from django.urls import path, include
from .views import *

urlpatterns = [
    path('', home, name='home'),
    path('card-demo', card_demo, name='card-demo'),
    path('about', about, name='about'),
]