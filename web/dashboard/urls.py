from django.urls import path, include
from django.shortcuts import redirect
from .views import *
from .topic_views import *

urlpatterns = [
    path('', lambda request: redirect('tasks', permanent=False), name='dashboard'),
    path('tasks', tasks, name='tasks'),
    path('queries', queries, name='queries'),
    path('tasks/detail/<int:id>', task_detail, name='task_detail'),
    path('tasks/create/', select_task, name='task_select'),
    path('tasks/create/<str:task_id>', create_task, name='task_create'),
    path('tasks/delete/', delete_task, name='task_delete'),
    path('tasks/delete-all/', delete_all_finished, name='task_delete_all'),
    # path('data-sanitizing', data_sanitizing, name='data-sanitizing'),
    path('data-import', data_import, name='data_import'),
    path('data-import/delete-archive/<path:archive_path>', delete_archive, name='delete_archive'),
    path('locations', locations, name='locations'),
    path('locations/<int:id>', show_location, name='show-location'),
    path('locations/delete/<int:location_id>', delete_location, name='delete_location'),
    path('locations/delete-membership/', delete_location_membership, name='delete_location_membership'),
    path('locations/edit/<int:location_id>', edit_location, name='edit_location'),
    path('locations/add/<path:doi>', add_location, name='add_location'),
    path('language-detection', language_detection, name='language-detection'),
    path('topics', topics_overview, name='topics'),
    path('topic/<int:topic_id>', papers_for_topic, name='topic_papers'),
    path('topics-merge', merge_topics, name='topics_merge'),
    path('topics-merge-generated', merge_generated, name='topics_merge_generated'),
    path('topic/<int:topic_id>/set-name', set_topic_name, name='set-topic-name'),
]
