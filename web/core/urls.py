from django.urls import path, include
from .views import *
from django.views.generic import TemplateView

urlpatterns = [
    path('', home, name='home'),
    path('categories', category_overview, name='category-overview'),
    path('about', about, name='about'),
    path('map', world_map, name='map'),
    path('imprint/', imprint, name='imprint'),
    path('privacy/', privacy, name='privacy'),
    path('paper/<path:doi>', paper, name='paper'),
    path('visualize/', embedding_visualization, name='embedding-visualization'),
    path('visualize/<int:topic_pk>', embedding_visualization, name='embedding-visualization-for-topic'),
    path('visualize/<path:doi>', embedding_visualization, name='embedding-visualization-for-doi'),
    path('paper-cards/', paper_cards, name='receive-papers'),
    path('robots.txt', TemplateView.as_view(template_name="core/robots.txt", content_type='text/plain')),
]
