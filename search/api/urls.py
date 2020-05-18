from django.urls import path
from .views import search, startup_probe

urlpatterns = [
    path('', search),
    path('status', startup_probe)
]
