import re
from time import sleep

import arxiv
import datetime

from django.utils.dateparse import parse_datetime
from nameparser import HumanName

from data.models import DataSource
from src.updater.data_updater import ArticleDataPoint, DataUpdater

_ARXIV_DATA_PRIORITY = 2
_ARXIV_PAPERHOST_NAME = 'arXiv'
_ARXIV_PAPERHOST_URL = 'https://www.arxiv.org'


def _get_arxiv_id_from_url(url):
    reduced_url = re.sub(r'v(\d+)$', '', url)
    splits = reduced_url.split('/abs/')
    if len(splits) < 2:
        return None
    else:
        return 'arXiv:' + splits[1]

class ArxivDataPoint(ArticleDataPoint):
    _ARXIV_WITHDRAWN_NOTICE = 'This paper has been withdrawn by the author(s)'

    def __init__(self, raw_article_dict):
        super().__init__()
        self.raw_article = raw_article_dict

    @property
    def doi(self):
        return _get_arxiv_id_from_url(self.raw_article['id'])

    @property
    def title(self):
        return self.raw_article['title'].replace('\n', ' ')

    @property
    def abstract(self):
        return self.raw_article['summary'].replace('\n', ' ')

    def extract_authors(self):
        authors = []
        for author in self.raw_article['authors']:
            human_name = HumanName(author)
            first_name = f'{human_name.first} {human_name.middle}'.strip()
            last_name = human_name.last
            authors.append((last_name, first_name))
        return authors

    def extract_content(self):
        return None

    @property
    def data_source(self):
        return DataSource.ARXIV

    @property
    def paperhost_name(self):
        return _ARXIV_PAPERHOST_NAME

    @property
    def paperhost_url(self):
        return _ARXIV_PAPERHOST_URL

    @property
    def published_at(self):
        return parse_datetime(self.raw_article['published']).date()

    @property
    def url(self):
        return self.raw_article['id']

    @property
    def pdf_url(self):
        return self.raw_article['pdf_url']

    @property
    def version(self):
        version_match = re.match('^\S+v(\d+)$', self.raw_article['id'])
        if version_match:
            return version_match.group(1)
        else:
            return '1'

    @property
    def is_preprint(self):
        return True


class ArxivUpdater(DataUpdater):
    _ARXIV_SEARCH_QUERY = 'title:"COVID 19" OR title:"SARS-CoV-2" OR title:"coronavirus" ' \
                          'OR abs:"COVID 19" OR abs:"SARS-CoV-2" OR abs:"coronavirus"'

    def __init__(self, log=print):
        super().__init__(log)
        self._query_result = None

    @property
    def data_source(self):
        return DataSource.ARXIV

    def _load_query_result(self):
        if not self._query_result:
            chunk_size = 500
            start = 0
            query_result = arxiv.query(self._ARXIV_SEARCH_QUERY, start=start, max_results=chunk_size, iterative=False,
                                       sort_by='submittedDate',
                                       sort_order='descending')
            self._query_result = [x for x in query_result
                                  if parse_datetime(x['updated']).date() >= datetime.date(2019, 12, 1)]

            while len(query_result) == chunk_size:
                # Fetch the remaining papers.
                # Make sure to follow arxiv API guidelines of at least 3 seconds between 2 queries.
                sleep(3)
                start += chunk_size
                query_result = arxiv.query(self._ARXIV_SEARCH_QUERY, start=start, max_results=chunk_size,
                                           iterative=False,
                                           sort_by='submittedDate',
                                           sort_order='descending')
                self._query_result += [x for x in query_result
                                       if parse_datetime(x['updated']).date() >= datetime.date(2019, 12, 1)]

    def _count(self):
        self._load_query_result()
        return len(self._query_result)

    def _get_all_articles(self):
        self._load_query_result()
        for article in self._query_result:
            yield ArxivDataPoint(raw_article_dict=article)

    def _get_article(self, doi):
        self._load_query_result()
        try:
            return ArxivDataPoint(next(x for x in self._query_result if _get_arxiv_id_from_url(x['id']) == doi))
        except StopIteration:
            return None
