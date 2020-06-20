from django.urls import path
from .views import search, startup_probe, similar

urlpatterns = [
    path('', search),
    path('similar', similar),
    path('status', startup_probe)
]
