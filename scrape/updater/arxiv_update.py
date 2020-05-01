import re
import arxiv

from nameparser import HumanName
from django.utils.dateparse import parse_datetime

from scrape.updater.data_updater import ArticleDataPoint, DataUpdater


class ArxivDataPoint(ArticleDataPoint):
    _ARXIV_DATA_SOURCE_NAME = 'arxiv-updater'
    _ARXIV_DATA_PRIORITY = 10
    _ARXIV_PAPERHOST_NAME = 'arXiv'
    _ARXIV_PAPERHOST_URL = 'https://www.arxiv.org'

    _ARXIV_WITHDRAWN_NOTICE = 'This paper has been withdrawn by the author(s)'

    def __init__(self, raw_article_dict):
        self.raw_article = raw_article_dict

    @property
    def doi(self):
        reduced_url = re.sub(r'v(\d+)$', '', self.raw_article['id'])
        splits = reduced_url.split('/abs/')
        if len(splits) < 2:
            return None
        else:
            return splits[1]

    @property
    def title(self):
        return self.raw_article['title'].replace('\n', ' ')

    @property
    def abstract(self):
        return self.raw_article['summary'].replace('\n', ' ')

    @property
    def authors(self):
        authors = []
        for author in self.raw_article['authors']:
            human_name = HumanName(author)
            first_name = f'{human_name.first} {human_name.middle}'.strip()
            last_name = human_name.last
            authors.append((last_name, first_name))
        return authors

    @property
    def content(self):
        return None

    @property
    def data_source_name(self):
        return self._ARXIV_DATA_SOURCE_NAME

    @property
    def data_source_priority(self):
        return self._ARXIV_DATA_PRIORITY

    @property
    def paperhost_name(self):
        return self._ARXIV_PAPERHOST_NAME

    @property
    def paperhost_url(self):
        return self._ARXIV_PAPERHOST_URL

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
            return int(version_match.group(1))
        else:
            return 1

    @property
    def is_preprint(self):
        return True


class ArxivUpdater(DataUpdater):
    _ARXIV_SEARCH_QUERY = 'all:%22COVID 19%22'
    _ARXIV_DATA_SOURCE_NAME = 'arxiv-updater'

    @property
    def _data_source_name(self):
        return self._ARXIV_DATA_SOURCE_NAME

    def __init__(self):
        super().__init__()
        self._query_result = arxiv.query(self._ARXIV_SEARCH_QUERY, max_results=1000, iterative=False,
                                         sort_by='submittedDate',
                                         sort_order='descending')
        # TODO: Split the query into smaller chunks?? Take a deeper look in arxiv package.

    @property
    def _data_points(self):
        for article in self._query_result:
            yield ArxivDataPoint(raw_article_dict=article)

    def _get_data_point(self, doi):
        for article in self._query_result:
            if article['doi'] == doi:
                return ArxivDataPoint(raw_article_dict=article)
        return None
