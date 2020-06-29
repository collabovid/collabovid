from django.urls import path, include
from .views import *

urlpatterns = [
    path('search', search, name='search'),
    path('authors', list_authors, name='get-authors'),
    path('journals', list_journals, name='get-journals'),
    path('locations', list_locations, name='get-locations'),
]