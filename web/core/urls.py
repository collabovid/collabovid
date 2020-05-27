from django.urls import path, include
from .views import *

urlpatterns = [
    path('', home, name='home'),
    path('search', search, name='search'),
    path('authors', list_authors, name='get-authors'),
    path('about', about, name='about'),
    path('topic/<int:id>', topic, name='topic'),
    path('topics/', topic_overview, name='topic-overview'),
    path('imprint/', imprint, name='imprint'),
    path('privacy/', privacy, name='privacy'),
]