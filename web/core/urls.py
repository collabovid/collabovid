from django.urls import path, include
from .views import *
from django.views.generic import TemplateView
from django.views.decorators.cache import cache_page

DEFAULT_CACHE_TIME = 60 * 15
LONG_CACHE_TIME = 60 * 60 * 2

urlpatterns = [
    path('', cache_page(DEFAULT_CACHE_TIME)(home), name='home'),
    path('categories', cache_page(DEFAULT_CACHE_TIME)(category_overview), name='category-overview'),
    path('about', cache_page(DEFAULT_CACHE_TIME)(about), name='about'),
    path('map', cache_page(DEFAULT_CACHE_TIME)(world_map), name='map'),
    path('imprint/', cache_page(LONG_CACHE_TIME)(imprint), name='imprint'),
    path('privacy/', cache_page(LONG_CACHE_TIME)(privacy), name='privacy'),
    path('paper/<path:doi>', paper, name='paper'),
    path('visualize/', cache_page(DEFAULT_CACHE_TIME)(embedding_visualization), name='embedding-visualization'),
    path('visualize/<int:topic_pk>', embedding_visualization, name='embedding-visualization-for-topic'),
    path('visualize/<path:doi>', embedding_visualization, name='embedding-visualization-for-doi'),
    path('paper-cards/', paper_cards, name='receive-papers'),
    path('robots.txt', TemplateView.as_view(template_name="core/robots.txt", content_type='text/plain')),
]
