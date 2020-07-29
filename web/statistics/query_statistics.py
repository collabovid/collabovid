from search.models import SearchQuery
from data.models import Topic, Category, Journal

from collections import defaultdict
from django.db.models import Count, QuerySet, F, Q
from django.core.serializers.json import DjangoJSONEncoder
import json
from django.utils.timezone import datetime, timedelta


class SearchQueryStatistics:

    def __init__(self, search_queries: QuerySet):
        self._search_queries = search_queries
        self._available = self._search_queries.count() > 0

        self._time_data = None
        self._tab_data = None
        self._recent_unique_queries = None

        self._distribution_data = dict()
        self._top_options_data = dict()

    @property
    def available(self):
        return self._available

    @property
    def time_data(self):
        if not self._time_data:
            self._time_data = defaultdict(list)
            for query_count in self._search_queries.extra(select={'created_at_date': 'date(created_at)'}) \
                    .values('created_at_date').annotate(queries_added=Count('*')).order_by('created_at_date'):
                self._time_data['x'].append(query_count['created_at_date'])
                self._time_data['added'].append(query_count['queries_added'])
                self._time_data['total'].append(sum(self._time_data['added']))
            self._time_data = json.dumps(self._time_data, cls=DjangoJSONEncoder)
        return self._time_data

    def distribution_data(self, key):
        if key not in self._distribution_data:
            distinct_options = [value[key] for value in self._search_queries.values(key).distinct()]
            print(distinct_options)
            self._distribution_data[key] = {
                option: self._search_queries.filter(**{key: option}).count() for option in distinct_options
            }
            self._distribution_data[key] = json.dumps(self._distribution_data[key], cls=DjangoJSONEncoder)
        return self._distribution_data[key]

    @property
    def tab_data(self):
        return self.distribution_data('query__tab')

    @property
    def sorted_data(self):
        return self.distribution_data('query__sorted_by')

    @property
    def article_type_data(self):
        return self.distribution_data('query__article_type')

    def top_options(self, key, model_cls, top=8):
        if key not in self._top_options_data:
            options = {obj.pk: obj.name for obj in model_cls.objects.all()}
            results = {
                options[option]: self._search_queries.filter(**{key + '__contains': option}).count() for option in
                options.keys()
            }
            self._top_options_data[key] = {k: v for k, v in sorted(results.items(), key=lambda x: x[1], reverse=True)[:top]}
            self._top_options_data[key] = json.dumps(self._top_options_data[key], cls=DjangoJSONEncoder)

        return self._top_options_data[key]

    def top_categories(self):
        return self.top_options(key='query__categories', model_cls=Category)

    def top_topics(self):
        return self.top_options(key='query__topics', model_cls=Topic)

    @property
    def recent_unique_queries(self):
        if not self._recent_unique_queries:
            self._recent_unique_queries = self._search_queries.order_by('-created_at').exclude(query__query='')[:100]
            print(self._recent_unique_queries)
        return self._recent_unique_queries

    @property
    def query_count(self):
        return self._search_queries.count()
