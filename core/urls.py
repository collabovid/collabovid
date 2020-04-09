from django.urls import path, include
from .views import *

urlpatterns = [
    path('', home, name='home'),
    path('explore', explore, name='explore'),
    path('about', about, name='about'),
    path('topic/<int:id>', topic, name='topic'),
    path('paper/<path:doi>', paper, name='paper'),
    path('topics/', topic_overview, name='topic-overview'),
    path('imprint/', imprint, name='imprint'),
]