from django.urls import path, include
from .views import *

urlpatterns = [
    path('', home, name='home'),
    path('search', search, name='search'),
    path('categories', category_overview, name='category-overview'),
    path('geo', geo, name='geo'),
    path('authors', list_authors, name='get-authors'),
    path('journals', list_journals, name='get-journals'),
    path('about', about, name='about'),
    path('imprint/', imprint, name='imprint'),
    path('privacy/', privacy, name='privacy'),
]