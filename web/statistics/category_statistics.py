from collections import defaultdict

from django.db.models import Count

from data.models import Category
from datetime import timedelta, datetime
from django.utils import timezone
from . import PaperStatistics

from django.core.serializers.json import DjangoJSONEncoder
import json

from django.db.models.functions import ExtractWeek, ExtractYear


class CategoryStatistics:
    """
    Computes some useful category statistics
    """

    def __init__(self, category: Category):
        self._category = category
        self._published_at_plot_data = None

    @property
    def pk(self):
        return self._category.pk

    @property
    def name(self):
        return self._category.name

    @property
    def color(self):
        return self._category.color

    @property
    def description(self):
        return self._category.description

    @property
    def paper_count(self):
        return self._category.papers.count()

    @property
    def paper_count_past_week(self):
        past_week = timezone.now().date() - timedelta(days=7)
        return self._category.papers.filter(published_at__gte=past_week).count()

    @property
    def paper_count_past_month(self):
        past_week = timezone.now().date() - timedelta(days=30)
        return self._category.papers.filter(published_at__gte=past_week).count()

    @property
    def paper_statistics(self):
        return PaperStatistics(self._category.papers)

    @property
    def published_at_complete(self):

        if not self._published_at_plot_data:

            published_at_plot_data = dict()
            published_at_plot_data['label'] = self.name
            published_at_plot_data['color'] = self.color

            published_at_plot_data['x'] = list()
            published_at_plot_data['total'] = list()

            start_date = datetime(2020, 1, 1)
            delta = datetime.now().date() - start_date.date()

            for i in range(int((delta.days + 1) / 7 + 1)):
                year = (start_date + timedelta(days=i*7)).isocalendar()[0]
                week = (start_date + timedelta(days=i*7)).isocalendar()[1]
                published_at_plot_data['x'].append({
                    "year": year,
                    "week": week
                })
                published_at_plot_data['total'].append(0)

            for published_count in self._category.papers.filter(published_at__gt=start_date) \
                    .annotate(year=ExtractYear('published_at'))\
                    .annotate(week=ExtractWeek('published_at')).values('year',
                    'week').annotate(papers_added=Count('doi')).order_by('year','week'):

                try:
                    index = published_at_plot_data['x'].index({
                        "year": published_count['year'],
                        "week": published_count['week']
                    })

                    published_at_plot_data['total'][index] = published_count['papers_added']
                except ValueError:
                    print("Not found ", published_count['published_at'])

            self._published_at_plot_data = json.dumps(published_at_plot_data, cls=DjangoJSONEncoder)

        return self._published_at_plot_data

    @property
    def newest_paper(self):
        return self._category.papers.latest('published_at', 'created_at')
