from django.db.models import F, QuerySet

from data.models import Paper
from math import ceil

from src.search.elasticsearch import ElasticsearchRequestHelper
from django.conf import settings


class VirtualPaginator:
    """
    This class abstracts a paginator and its main purpose is to compute the correct
    page the user searches for and computing highlights that are placed alongside the correctly ordered
    pages as a json result.
    """
    PAPER_PAGE_COUNT = 10

    def __init__(self, search_results: dict, form: dict):

        self._form = form

        if form['sorted_by'] == 'newest' or (form['sorted_by'] == 'top' and not form['query'].strip()):
            self.sorted_dois = Paper.objects.filter(pk__in=search_results.keys()).order_by("-published_at",                                                                              "-created_at")
        elif form['sorted_by'] == 'top':
            self.sorted_dois = sorted(search_results.keys(), key=lambda x: search_results[x], reverse=True)
        elif form['sorted_by'] == 'popularity':
            self.sorted_dois = Paper.objects.filter(pk__in=search_results.keys()).order_by(
                F('altmetric_data__score').desc(nulls_last=True)
            )
        elif form['sorted_by'].startswith('trending'):
            span = form['sorted_by'][9:]
            if span not in ('d', 'w', '1m', '3m', '6m', 'y'):
                raise ValueError("Sorted by has unknown value" + str(form['sorted_by']))

            sort_key = f'altmetric_data__score_{span}'
            self.sorted_dois = Paper.objects.filter(pk__in=search_results.keys()).order_by(
                F(sort_key).desc(nulls_last=True)
            )
        else:
            raise ValueError("Sorted by has unknown value" + str(form['sorted_by']))

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
            dois_for_page = list(self.sorted_dois[bottom:top].values_list('doi', flat=True))
        else:
            dois_for_page = self.sorted_dois[bottom:top]

        paginator = self.build_paginator()
        paginator['page'] = self._form['page']
        paginator['results'] = list()
        paginator['authors'] = list()

        if len(dois_for_page) > 0:
            results = {doi: {'order': i, 'doi': doi} for i, doi in enumerate(dois_for_page)}
            authors = []

            if settings.USING_ELASTICSEARCH:
                ElasticsearchRequestHelper.highlights(results, self._form['query'], ids=dois_for_page)
                ElasticsearchRequestHelper.find_authors(authors, self._form['query'], self._form['authors'])

            paginator['results'] = sorted(list(results.values()), key=lambda x: x['order'])
            paginator['authors'] = authors

        return paginator
