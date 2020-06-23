from django.urls import path, include
from .views import *

urlpatterns = [
    path('', home, name='home'),
    path('categories', category_overview, name='category-overview'),
    path('about', about, name='about'),
    path('map', world_map, name='map'),
    path('imprint/', imprint, name='imprint'),
    path('privacy/', privacy, name='privacy'),
    path('paper/<path:doi>', paper, name='paper'),
]