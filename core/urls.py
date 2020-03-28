from django.urls import path, include
from .views import *

urlpatterns = [
    path('', home, name='home'),
    path('about', about, name='about'),
    path('scrape', scrape, name='scrape'),
]