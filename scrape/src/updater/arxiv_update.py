import re
from time import sleep

import arxiv
import datetime

from django.utils.dateparse import parse_datetime
from nameparser import HumanName

from data.models import DataSource
from src.updater.data_updater import DataUpdater
from data.paper_db_insert import SerializableArticleRecord

_ARXIV_PAPERHOST_NAME = 'arXiv'


def _get_arxiv_id_from_url(url):
    reduced_url = re.sub(r'v(\d+)$', '', url)
    splits = reduced_url.split('/abs/')
    if len(splits) < 2:
        return None
    else:
        return 'arXiv:' + splits[1]


class ArxivUpdater(DataUpdater):
    _ARXIV_SEARCH_QUERY = 'title:"COVID 19" OR title:"SARS-CoV-2" OR title:"coronavirus" ' \
                          'OR abs:"COVID 19" OR abs:"SARS-CoV-2" OR abs:"coronavirus"'

    def __init__(self, log=print, pdf_image=False, pdf_content=False, update_existing=False):
        super().__init__(log, pdf_image=pdf_image, pdf_content=pdf_content, update_existing=update_existing)
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

    def _extract_authors(self, raw_data):
        authors = []
        for author in raw_data['authors']:
            human_name = HumanName(author)
            first_name = f'{human_name.first} {human_name.middle}'.strip()
            last_name = human_name.last
            if first_name or last_name:
                authors.append((last_name, first_name))
        return authors

    def _create_serializable_record(self, raw_data):
        """ Construct a serializable record from a given result of the arxiv package """
        article = SerializableArticleRecord(doi=_get_arxiv_id_from_url(raw_data['id']),
                                   title=raw_data['title'].replace('\n', ' '),
                                   abstract=raw_data['summary'].replace('\n', ' '),
                                   is_preprint=True)
        article.paperhost = _ARXIV_PAPERHOST_NAME
        article.datasource = DataSource.ARXIV
        article.url = raw_data['id']
        article.publication_date = parse_datetime(raw_data['published']).date()

        version_match = re.match('^\S+v(\d+)$', raw_data['id'])
        if version_match:
            article.version = version_match.group(1)
        else:
            article.version = '1'

        article.pdf_url = raw_data['pdf_url']
        article.authors = self._extract_authors(raw_data)

        return article

    def _get_data_points(self):
        self._load_query_result()
        for article in self._query_result:
            yield self._create_serializable_record(raw_data=article)

    def _get_data_point(self, doi):
        self._load_query_result()
        try:
            return self._create_serializable_record(next(x for x in self._query_result
                                                         if _get_arxiv_id_from_url(x['id']) == doi))
        except StopIteration:
            return None
