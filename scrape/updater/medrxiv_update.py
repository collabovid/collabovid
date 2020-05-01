import json
import re
from typing import Callable, List, Tuple, Any

import requests
from bs4 import BeautifulSoup

from data.models import Paper
from datetime import datetime
from scrape.updater.data_updater import ArticleDataPoint, DataUpdater


class MedrxivDataPoint(ArticleDataPoint):
    _MEDRXIV_DATA_SOURCE_NAME = 'medrxiv-updater'
    _MEDRXIV_DATA_PRIORITY = 5

    _MEDRXIV_PAPERHOST_NAME = 'medRxiv'
    _MEDRXIV_PAPERHOST_URL = 'https://www.medrxiv.org'
    _BIORXIV_PAPERHOST_NAME = 'bioRxiv'
    _BIORXIV_PAPERHOST_URL = 'https://www.biorxiv.org'

    def __init__(self, raw_article_json):
        self.raw_article = raw_article_json
        self._article_soup = None

    def _setup_article_soup(self):
        if not self._article_soup:
            response = requests.get(self.url)
            self._article_soup = BeautifulSoup(response.text, 'html.parser')
            self.redirected_url = response.url

    @property
    def doi(self):
        return self.raw_article['rel_doi']

    @property
    def title(self):
        return self.raw_article['rel_title']

    @property
    def abstract(self):
        return self.raw_article['rel_abs']

    @property
    def authors(self):
        self._setup_article_soup()

        author_webelements = self._article_soup.find(
            'span', attrs={'class': 'highwire-citation-authors'}
        ).find_all('span', recursive=False)

        authors = []
        for author_webelement in author_webelements:
            try:
                firstname = author_webelement.find('span', attrs={'class': 'nlm-given-names'}).text
                name = author_webelement.find('span', attrs={'class': 'nlm-surname'}).text
                authors.append((name, firstname))
            except AttributeError:
                # Ignore collaboration groups, listed in authors list
                continue
        return authors

    @property
    def content(self):
        return None

    @property
    def data_source_name(self):
        return self._MEDRXIV_DATA_SOURCE_NAME

    @property
    def data_source_priority(self):
        return self._MEDRXIV_DATA_PRIORITY

    @property
    def paperhost_name(self):
        site = self.raw_article['rel_site']
        if site == "medrxiv":
            return self._MEDRXIV_PAPERHOST_NAME
        elif site == "biorxiv":
            return self._BIORXIV_PAPERHOST_NAME
        else:
            return None

    @property
    def paperhost_url(self):
        if self.paperhost_name == self._MEDRXIV_PAPERHOST_NAME:
            return self._MEDRXIV_PAPERHOST_URL
        else:
            return self._BIORXIV_PAPERHOST_URL

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

        version_match = re.match('^\S+v(\d+)$', self.redirected_url)
        if version_match:
            return int(version_match.group(1))
        else:
            return 1

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
    _MEDRXIV_DATA_SOURCE_NAME = 'medrxiv-updater'
    _COVID_JSON_URL = 'https://connect.medrxiv.org/relate/collection_json.php?grp=181'

    @property
    def _data_source_name(self):
        return self._MEDRXIV_DATA_SOURCE_NAME

    def __init__(self):
        super().__init__()
        self._article_json = self._get_article_json()

    def _get_article_json(self):
        try:
            response = requests.get(self._COVID_JSON_URL)
            return json.loads(response.text)['rels']
        except requests.exceptions.ConnectionError as ex:
            raise Exception("Unable to download medRxiv COVID-19 article list JSON")

    @property
    def _data_points(self):
        for article in self._article_json:
            yield MedrxivDataPoint(raw_article_json=article)

    def _get_data_point(self, doi):
        for article in self._article_json:
            if article['rel_doi'] == doi:
                return MedrxivDataPoint(raw_article_json=article)
        return None


# TODO:
#  - integrate revoked articles into above process?
def delete_revoked_articles(log_function: Callable[[Tuple[Any, ...]], Any] = print) -> List[str]:
    """
    Remove all revoked articles (no longer in JSON file) from DB.

    :return: List of dois of removed articles.
    """
    json_dois = [article['rel_doi'] for article in _get_article_json()]

    revoked_articles = []
    for db_article in Paper.objects.all():
        if db_article.doi not in json_dois:
            revoked_articles.append(db_article.doi)
            log_function(f"Deleting article {db_article.doi}")

    Paper.objects.filter(doi__in=revoked_articles).delete()

    log_function(f"Deleted {len(revoked_articles)} articles")
    return revoked_articles
