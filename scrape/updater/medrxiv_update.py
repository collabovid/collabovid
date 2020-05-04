import json
import re

import requests
from bs4 import BeautifulSoup

from data.models import DataSource
from datetime import datetime
from scrape.updater.data_updater import ArticleDataPoint, DataUpdater

from multiprocessing import Pool as ThreadPool

_MEDRXIV_PAPERHOST_NAME = 'medRxiv'
_BIORXIV_PAPERHOST_NAME = 'bioRxiv'
_MEDRXIV_PAPERHOST_URL = 'https://www.medrxiv.org'
_BIORXIV_PAPERHOST_URL = 'https://www.biorxiv.org'
_MEDBIORXIV_DATA_PRIORITY = 1


class MedrxivDataPoint(ArticleDataPoint):
    def __init__(self, raw_article_json, response):
        super().__init__()
        self.raw_article = raw_article_json
        self._article_soup = None
        self.response=response

    def _setup_article_soup(self):
        if not self._article_soup:
            #response = requests.get(self.url)
            self._article_soup = BeautifulSoup(self.response.text, 'html.parser')
            self.redirected_url = self.response.url

    @property
    def doi(self):
        return self.raw_article['rel_doi']

    @property
    def title(self):
        return self.raw_article['rel_title']

    @property
    def abstract(self):
        return self.raw_article['rel_abs']

    def extract_authors(self):
        self._setup_article_soup()

        author_webelements = self._article_soup.find(
            'span', attrs={'class': 'highwire-citation-authors'}
        ).find_all('span', recursive=False)

        authors = []
        for author_webelement in author_webelements:
            try:
                firstname = author_webelement.find('span', attrs={'class': 'nlm-given-names'}).text
                lastname = author_webelement.find('span', attrs={'class': 'nlm-surname'}).text
                authors.append((lastname, firstname))
            except AttributeError:
                # Ignore collaboration groups, listed in authors list
                continue
        return authors


    @property
    def data_source_name(self):
        return DataSource.MEDBIORXIV_DATASOURCE_NAME

    @property
    def data_source_priority(self):
        return _MEDBIORXIV_DATA_PRIORITY

    @property
    def paperhost_name(self):
        site = self.raw_article['rel_site']
        if site == "medrxiv":
            return _MEDRXIV_PAPERHOST_NAME
        elif site == "biorxiv":
            return _BIORXIV_PAPERHOST_NAME
        else:
            return None

    @property
    def paperhost_url(self):
        if self.paperhost_name == _MEDRXIV_PAPERHOST_NAME:
            return _MEDRXIV_PAPERHOST_URL
        else:
            return _BIORXIV_PAPERHOST_URL

    @property
    def published_at(self):
        return datetime.strptime(self.raw_article['rel_date'], "%Y-%m-%d").date()

    @property
    def url(self):
        return self.raw_article['rel_link']

    @property
    def pdf_url(self):
        self._setup_article_soup()

        dl_element = self._article_soup.find('a', attrs={'class': 'article-dl-pdf-link link-icon'})
        if dl_element and dl_element.has_attr('href'):
            relative_url = dl_element['href']
            return self.paperhost_url + relative_url
        else:
            return None

    @property
    def version(self):
        self._setup_article_soup()

        version_match = re.match(r'^\S+v(\d+)$', self.redirected_url)
        if version_match:
            return version_match.group(1)
        else:
            return '1'

    @property
    def is_preprint(self):
        return True

    @property
    def category_name(self):
        self._setup_article_soup()
        categories = self._article_soup.find_all('span', {'class': 'highwire-article-collection-term'})
        if len(categories) == 0:
            return "Unknown"
        else:
            return categories[0].text.strip()


class MedrxivUpdater(DataUpdater):
    _COVID_JSON_URL = 'https://connect.medrxiv.org/relate/collection_json.php?grp=181'

    @property
    def _data_source_name(self):
        return DataSource.MEDBIORXIV_DATASOURCE_NAME

    def __init__(self, log=print):
        super().__init__(log)
        self._article_json = None

    def _get_article_json(self):
        if not self._article_json:
            try:
                response = requests.get(self._COVID_JSON_URL)
                self._article_json = json.loads(response.text)['rels'][:50]
            except requests.exceptions.ConnectionError:
                raise Exception("Unable to download medRxiv COVID-19 article list JSON")

    def _count(self):
        self._get_article_json()
        return len(self._article_json)

    def _get_data_points(self):
        self._get_article_json()

        chunk_size = 100
        for i in range(0, len(self._article_json), chunk_size):
            urls = [x['rel_link'] for x in self._article_json[i:i + chunk_size]]
            pool = ThreadPool(16)
            responses = pool.map(requests.get, urls)
            pool.close()
            pool.join()

            for article in zip(self._article_json[i:i + chunk_size], responses):
                yield MedrxivDataPoint(*article)

    def _get_data_point(self, doi):
        self._get_article_json()
        try:
            return MedrxivDataPoint(next(x for x in self._article_json if x['rel_doi'] == doi))
        except StopIteration:
            return None
