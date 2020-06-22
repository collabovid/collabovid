from django.urls import path, include
from .views import *

urlpatterns = [
    path('', home, name='home'),
    path('search', search, name='search'),
    path('categories', category_overview, name='category-overview'),
    path('map', locations, name='map'),
    path('authors', list_authors, name='get-authors'),
    path('journals', list_journals, name='get-journals'),
    path('locations', list_locations, name='get-locations'),
    path('about', about, name='about'),
    path('imprint/', imprint, name='imprint'),
    path('privacy/', privacy, name='privacy'),
    path('paper/<path:doi>', paper, name='paper'),
    path('embedding-visualization/', embedding_visualization, name='embedding-visualization'),
    path('paper-cards/', paper_cards, name='paper-cards'),
]
