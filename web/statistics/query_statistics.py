from search.models import SearchQuery
from data.models import Topic, Category, Journal, PaperHost, GeoLocation, Author

from collections import defaultdict
from django.db.models import Count, QuerySet
from django.core.serializers.json import DjangoJSONEncoder
import json


class SearchQueryStatistics:
    """
    Class that computes statistics over the search queries.
    """
    FILTER_ARRAY_KEYS = ['locations', 'categories', 'journals', 'paper_hosts', 'topics', 'authors']

    def __init__(self, search_queries: QuerySet):
        self._search_queries = search_queries
        self._available = self._search_queries.count() > 0

        self._time_data = None
        self._tab_data = None
        self._recent_unique_queries = None

        self._distribution_data = dict()
        self._full_query_data = None

    @property
    def available(self):
        return self._available

    @property
    def full_query_data(self):
        if not self._full_query_data:
            counter = {k: defaultdict(int) for k in SearchQueryStatistics.FILTER_ARRAY_KEYS}
            filter_count_distribution = defaultdict(int)
            filter_type_counts = defaultdict(int)
            filter_lengths = defaultdict(dict)
            for search_query in self._search_queries:
                for key in counter.keys():
                    if key in search_query.query:
                        for value in search_query.query[key]:
                            counter[key][value] += 1
                applied_filters = self._applied_filters(search_query)
                for filter in applied_filters:
                    filter_type_counts[filter] += 1
                filter_count_distribution[len(applied_filters)] += 1
                for name, count in self._filter_length(search_query).items():
                    filter_lengths[count][name] = filter_lengths[count][name] + 1 if name in filter_lengths[
                        count] else 0

            self._full_query_data = {
                'counter': counter,
                'filter_distribution': filter_count_distribution,
                'filter_type_counts': filter_type_counts,
                'filter_lengths': filter_lengths
            }
        return self._full_query_data

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
            self._distribution_data[key] = {
                result[key]: result['count'] for result in self._search_queries.values(key).annotate(count=Count('*'))
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

    def top_options(self, identifier, model_cls, name_attribute='name', top=8):
        counter = self.full_query_data['counter']
        counts = sorted(counter[identifier].items(), key=lambda x: x[1], reverse=True)[:top]
        result = {}
        for pk, value in counts:
            try:
                model = model_cls.objects.get(pk=pk)
                result[getattr(model, name_attribute)] = value
            except model_cls.DoesNotExist:
                pass
        return json.dumps(result, cls=DjangoJSONEncoder)

    @property
    def top_categories(self):
        return self.top_options(identifier='categories', model_cls=Category)

    @property
    def top_topics(self):
        return self.top_options(identifier='topics', model_cls=Topic)

    @property
    def top_paper_hosts(self):
        return self.top_options(identifier='paper_hosts', model_cls=PaperHost)

    @property
    def top_locations(self):
        return self.top_options(identifier='locations', model_cls=GeoLocation, top=20)

    @property
    def top_journals(self):
        return self.top_options(identifier='journals', model_cls=Journal, top=20)

    @property
    def top_authors(self):
        return self.top_options(identifier='authors', model_cls=Author, name_attribute='full_name', top=20)

    @property
    def filter_distribution(self):
        return json.dumps(self.full_query_data['filter_distribution'], cls=DjangoJSONEncoder)

    @property
    def filter_type_counts(self):
        return json.dumps(self.full_query_data['filter_type_counts'], cls=DjangoJSONEncoder)

    @property
    def filter_lengths(self):
        filter_lengths = self.full_query_data['filter_lengths']
        result = []
        for lengths, count_by_name in filter_lengths.items():
            count_values = [0] * len(SearchQueryStatistics.FILTER_ARRAY_KEYS)
            for name, count in count_by_name.items():
                count_values[SearchQueryStatistics.FILTER_ARRAY_KEYS.index(name)] = count
            result.append(count_values)
        return json.dumps({'labels': SearchQueryStatistics.FILTER_ARRAY_KEYS, 'data': result}, cls=DjangoJSONEncoder)

    @property
    def recent_queries(self):
        if not self._recent_unique_queries:
            self._recent_unique_queries = self._search_queries.order_by('-created_at').exclude(query__query='')[:500]
        return self._recent_unique_queries

    @property
    def top_query_terms(self):
        return self._search_queries.values('query__query').annotate(count=Count('*')).order_by('-count')[:500]

    @property
    def query_count(self):
        return self._search_queries.count()

    def _applied_filters(self, query: SearchQuery):
        """
        Returns the filters that
        """
        filters = []
        for key in SearchQueryStatistics.FILTER_ARRAY_KEYS:
            if key in query.query and len(query.query[key]) > 0:
                filters.append(key)

        def is_not_default(identifier, default):
            return identifier in query.query and query.query[identifier] != default

        if is_not_default('article_type', 'all'):
            filters.append('article_type')

        if is_not_default('published_at_start', None) or is_not_default('published_at_end', None):
            filters.append('published_at')

        return filters

    def _filter_length(self, query: SearchQuery):
        """
        Returns the number of filter items (e.g. number of authors) for each possible filter
        """
        filter_count = defaultdict(int)
        for key in SearchQueryStatistics.FILTER_ARRAY_KEYS:
            if key in query.query and len(query.query[key]) > 0:
                filter_count[key] = len(query.query[key])

        return filter_count
