from django.urls import path
from .views import search, startup_probe, similar, search_similar

urlpatterns = [
    path('search', search),
    path('search/similar', search_similar),
    path('similar', similar),
    path('status', startup_probe)
]
