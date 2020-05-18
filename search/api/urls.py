from django.urls import path
from .views import search, startup_probe, liveness_probe

urlpatterns = [
    path('', search),
    path('status', startup_probe),
    path('alive', liveness_probe)
]
