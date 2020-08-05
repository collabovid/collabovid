from django.urls import path
from .views import *

urlpatterns = [
    path('search', search, name='search'),
    path('export/search/<str:export_type>', export_search_result, name='search-export'),
    path('export/<str:export_type>/<path:doi>', export_paper, name='export-paper'),
    path('analyze', literature_analysis, name='literature-analysis'),
    path('favorites', favorites, name='favorites'),
    path('favorite-analysis', favorite_analysis, name='favorite-analysis'),
    path('similar', similar_papers, name='similar-papers'),
    path('authors', list_authors, name='get-authors'),
    path('journals', list_journals, name='get-journals'),
    path('locations', list_locations, name='get-locations'),
    path('topics', list_topics, name='get-topics'),
]