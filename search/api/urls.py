from django.urls import path
from .views import search, startup_probe, similar, search_similar, find_topics

urlpatterns = [
    path('search', search),
    path('search/similar', search_similar),
    path('similar', similar),
    path('status', startup_probe),
    path('topic', find_topics)
]
