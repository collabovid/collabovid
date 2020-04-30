from search.search_engine import SearchResult
from data.models import Paper, Category, Topic, Author, PaperHost
import os
import requests

from django.conf import settings
from collections import defaultdict
from django.db.models import Count, QuerySet
from django.core.serializers.json import DjangoJSONEncoder
import json
from django.utils.timezone import datetime, timedelta


class Statistics:

    def __init__(self, papers: QuerySet):
        self._papers = papers
        self._published_at_plot_data = None
        self._paper_host_data = None
        self._category_data = None
        self._topic_data = None

        self._available = self._papers.count() > 0

    @property
    def available(self):
        return self._available

    @property
    def published_at_data(self):
        if not self._published_at_plot_data:
            self._published_at_plot_data = defaultdict(list)
            for published_count in self._papers.filter(published_at__gt=datetime(2020, 1, 1)).values(
                    'published_at').annotate(papers_added=Count('doi')).order_by('published_at'):
                self._published_at_plot_data['x'].append(published_count['published_at'])
                self._published_at_plot_data['added'].append(published_count['papers_added'])
                self._published_at_plot_data['total'].append(sum(self._published_at_plot_data['added']))

            self._published_at_plot_data = json.dumps(self._published_at_plot_data, cls=DjangoJSONEncoder)

        return self._published_at_plot_data

    @property
    def paper_host_data(self):
        if not self._paper_host_data:
            self._paper_host_data = json.dumps(
                {host.name: self._papers.filter(host=host).count() for host in PaperHost.objects.all() if
                 self._papers.filter(host=host).count() > 0},
                cls=DjangoJSONEncoder)

        return self._paper_host_data

    @property
    def category_data(self):
        if not self._category_data:
            self._category_data = json.dumps(
                {category.name: self._papers.filter(category=category).count() for category in Category.objects.all() if
                 self._papers.filter(category=category).count() > 0},
                cls=DjangoJSONEncoder)

        return self._category_data

    @property
    def topic_data(self):
        if not self._topic_data:
            self._topic_data = json.dumps(
                {topic.name: self._papers.filter(topic=topic).count() for topic in Topic.objects.all() if
                 self._papers.filter(topic=topic).count() > 0},
                cls=DjangoJSONEncoder)

        return self._topic_data

    @property
    def paper_count(self):
        return self._papers.count()

    @property
    def paper_host_count(self):
        return self._papers.filter(host__isnull=False).values('host').distinct().count()

    @property
    def topic_count(self):
        return self._papers.filter(topic__isnull=False).values('topic').distinct().count()

    @property
    def author_count(self):
        return self._papers.values('authors').distinct().count()

    @property
    def paper_today_count(self):
        date_from = datetime.now() - timedelta(days=1)
        return self._papers.filter(published_at__gt=date_from).count()

    @property
    def papers_last_week(self):
        date_from = datetime.now() - timedelta(days=7)
        return self._papers.filter(published_at__gt=date_from).count()
