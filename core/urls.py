from django.urls import path, include
from .views import *

urlpatterns = [
    path('', home, name='home'),
    path('explore', explore, name='explore'),
    path('about', about, name='about'),
    path('topic/<int:id>', topic, name='topic'),
    path('topics/', topic_overview, name='topic-overview'),
]