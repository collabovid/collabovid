from django.db.models.functions import ExtractWeek, Extract

from data.models import Topic

from collections import defaultdict
from django.db.models import Count, QuerySet, F, Q, DateTimeField
from django.core.serializers.json import DjangoJSONEncoder
import json
from django.utils.timezone import datetime, timedelta
from isoweek import Week


@DateTimeField.register_lookup
class ExtractISOYear(Extract):
    lookup_name = 'isoyear'


class PaperStatistics:

    def __init__(self, papers: QuerySet, ordered_papers: QuerySet = None):
        self._papers = papers
        self._ordered_papers = ordered_papers
        self._published_at_plot_data = None
        self._paper_host_data = None
        self._category_data = None
        self._topic_data = None
        self._has_category_data = None
        self._latest_date = None

        self._available = self._papers.count() > 0

    @property
    def papers(self):
        if self._ordered_papers:
            return self._ordered_papers

        return self._papers

    @property
    def latest_date(self):
        if self._latest_date is None:
            self._latest_date = self._papers.filter(published_at__lte=datetime.now().date()).latest(
                'published_at').published_at
        return self._latest_date

    @property
    def available(self):
        return self._available

    @property
    def published_at_data(self):
        if not self._published_at_plot_data:
            self._published_at_plot_data = defaultdict(list)
            for published_count in self._papers.filter(published_at__gt=datetime(2020, 1, 1)).annotate(
                    year=ExtractISOYear('published_at')).annotate(week=ExtractWeek('published_at')) \
                    .values('year', 'week').annotate(papers_added=Count('doi')).order_by('year', 'week'):

                self._published_at_plot_data['x'].append(Week(published_count['year'], published_count['week']).monday())

                self._published_at_plot_data['added'].append(published_count['papers_added'])
                self._published_at_plot_data['total'].append(sum(self._published_at_plot_data['added']))

            self._published_at_plot_data = json.dumps(self._published_at_plot_data, cls=DjangoJSONEncoder)

            print(self._published_at_plot_data)

        return self._published_at_plot_data

    @property
    def paper_host_data(self):
        if not self._paper_host_data:
            paper_hosts = self._papers.values('host').annotate(count=Count('*')).annotate(name=F('host__name'))

            self._paper_host_data = json.dumps(
                {host['name']: host['count'] for host in paper_hosts},
                cls=DjangoJSONEncoder)

        return self._paper_host_data

    @property
    def has_category_data(self):
        if self._has_category_data is None:
            self._has_category_data = self._papers.annotate(categories_count=Count('categories')) \
                .filter(categories_count__gt=0).exists()
        return self._has_category_data

    @property
    def category_data(self):
        if not self._category_data:
            categories = self._papers.annotate(name=F('categories__name'), color=F('categories__color')) \
                .values('name', 'color').annotate(count=Count('pk'))

            self._category_data = json.dumps({
                category['name']: {
                    'count': category['count'],
                    'color': category['color']
                }
                for category in categories if category['name'] is not None
            }, cls=DjangoJSONEncoder)

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
