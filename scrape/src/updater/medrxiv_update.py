import json
import re

import requests
from bs4 import BeautifulSoup

from data.models import DataSource, Paper
from datetime import datetime
from src.updater.data_updater import DataUpdater
from data.paper_db_insert import SerializableArticleRecord


_MEDRXIV_PAPERHOST_NAME = 'medRxiv'
_BIORXIV_PAPERHOST_NAME = 'bioRxiv'
_MEDRXIV_PAPERHOST_URL = 'https://www.medrxiv.org'
_BIORXIV_PAPERHOST_URL = 'https://www.biorxiv.org'


class MedrxivUpdater(DataUpdater):
    _COVID_JSON_URL = 'https://connect.medrxiv.org/relate/collection_json.php?grp=181'

    @property
    def data_source(self):
        return DataSource.MEDBIORXIV

    def __init__(self, log=print, pdf_image=False, pdf_content=False, update_existing=False):
        super().__init__(log, pdf_image=pdf_image, pdf_content=pdf_content, update_existing=update_existing)
        self._article_json = None

    def _get_article_json(self):
        if not self._article_json:
            try:
                response = requests.get(self._COVID_JSON_URL)
                self._article_json = json.loads(response.text)['rels']
            except requests.exceptions.ConnectionError:
                raise Exception("Unable to download medRxiv COVID-19 article list JSON")

    def _count(self):
        self._get_article_json()
        return len(self._article_json)

    def _extract_authors(self, article_soup):
        try:
            author_webelements = article_soup.find('span', attrs={'class': 'highwire-citation-authors'}).find_all(
                'span', recursive=False)
        except AttributeError:
            return []
        authors = []
        for author_webelement in author_webelements:
            try:
                firstname = author_webelement.find('span', attrs={'class': 'nlm-given-names'}).text
                lastname = author_webelement.find('span', attrs={'class': 'nlm-surname'}).text
                if firstname or lastname:
                    authors.append((lastname, firstname))
            except AttributeError:
                # Ignore collaboration groups, listed in authors list
                continue
        return authors

    def _create_serializable_record(self, raw_data, skip_existing=False):
        article = SerializableArticleRecord(doi=raw_data['rel_doi'], title=raw_data['rel_title'],
                                            abstract=raw_data['rel_abs'], is_preprint=True)
        if skip_existing and Paper.objects.filter(doi=article.doi).exists():
            return None

        site = raw_data['rel_site']
        if site == "medrxiv":
            article.paperhost = _MEDRXIV_PAPERHOST_NAME
            host_url = _MEDRXIV_PAPERHOST_URL
        elif site == "biorxiv":
            article.paperhost = _BIORXIV_PAPERHOST_NAME
            host_url = _BIORXIV_PAPERHOST_URL
        article.datasource = DataSource.MEDBIORXIV
        article.url = raw_data['rel_link']
        article.publication_date = datetime.strptime(raw_data['rel_date'], "%Y-%m-%d").date()

        response = requests.get(article.url)
        article_soup = BeautifulSoup(response.text, 'html.parser')
        redirected_url = response.url

        version_match = re.match(r'^\S+v(\d+)$', redirected_url)
        if version_match:
            article.version = version_match.group(1)
        else:
            article.version = '1'

        dl_element = article_soup.find('a', attrs={'class': 'article-dl-pdf-link link-icon'})
        if dl_element and dl_element.has_attr('href'):
            relative_url = dl_element['href']
            article.pdf_url = host_url + relative_url

        article.authors = self._extract_authors(article_soup)

        return article

    def _get_data_points(self):
        self._get_article_json()

        for article in self._article_json:
            record = self._create_serializable_record(article, skip_existing=True)
            if record:
                yield record
            else:
                # For medRxiv, it is required to skip articles before getting the author list, which would result in an
                # additional web request. For the case, the article already exists, the record is None.
                self.statistics.n_skipped += 1

    def _get_data_point(self, doi):
        self._get_article_json()
        try:
            return self._create_serializable_record(next(x for x in self._article_json if x['rel_doi'] == doi),
                                                    skip_existing=False)
        except StopIteration:
            return None
