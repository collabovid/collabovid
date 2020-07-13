from django.urls import path
from .views import *

urlpatterns = [
    path('search', search, name='search'),
    path('search/export', export_search_result, name='search-export'),
    path('upload', upload_ris, name='upload_ris'),
    path('similar', similar_papers, name='similar_papers'),
    path('authors', list_authors, name='get-authors'),
    path('journals', list_journals, name='get-journals'),
    path('locations', list_locations, name='get-locations'),
    path('topics', list_topics, name='get-topics'),
]