from django.db.models import QuerySet

from data.models import Paper
from math import ceil

from src.search.elasticsearch import Elasticsearch
from src.search.semantic_search import SemanticSearch


class VirtualPaginator:
    PAPER_PAGE_COUNT = 10

    def __init__(self, search_results: dict, form: dict):

        self._form = form
        if form['tab'] == 'newest':
            self.sorted_dois = Paper.objects.filter(pk__in=search_results.keys()).order_by("-published_at",
                                                                                           "-created_at")
        elif form['tab'] == 'top':
            self.sorted_dois = sorted(search_results.keys(), key=lambda x: search_results[x], reverse=True)

        if isinstance(self.sorted_dois, QuerySet):
            self.count = self.sorted_dois.count()
        else:
            self.count = len(self.sorted_dois)

        self.per_page = VirtualPaginator.PAPER_PAGE_COUNT
        self.num_pages = ceil(self.count / self.per_page)

    def build_paginator(self):

        return {
            'num_pages': self.num_pages,
            'per_page': self.per_page,
            'count': self.count
        }

    def get_page(self):

        bottom = (self._form['page'] - 1) * self.per_page
        top = bottom + self.per_page

        if isinstance(self.sorted_dois, QuerySet):
            dois_for_page = self.sorted_dois[bottom:top].values_list('doi', flat=True)
        else:
            dois_for_page = self.sorted_dois[bottom:top]

        paginator = self.build_paginator()
        paginator['page'] = self._form['page']

        results = {doi: {'order': i, 'doi': doi} for i, doi in enumerate(dois_for_page)}
        Elasticsearch().highlights(results, self._form['query'], ids=dois_for_page)
        SemanticSearch().compute_similars(results, self._form['query'], score_min=0.6)

        paginator['results'] = sorted(results.values(), key=lambda x: x['order'])

        return paginator
