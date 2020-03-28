from django.urls import path, include
from .views import *

urlpatterns = [
    path('', home, name='home'),
    path('search', search, name='search'),
    path('about', about, name='about'),
    path('scrape', scrape, name='scrape'),
    path('topic/<int:id>', topic, name='topic'),
]