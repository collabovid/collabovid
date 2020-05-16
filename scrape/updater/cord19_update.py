import csv
import json
import os
import shutil
import tarfile
from datetime import timedelta, datetime
from pathlib import Path
import random
from timeit import default_timer as timer

import requests

# TODO:
#   - Identify removed articles
from data.models import DataSource, PaperData
from scrape.updater.cord19.cord19_cache import Cord19Cache
from scrape.updater.data_updater import DataUpdater, ArticleDataPoint

_CORD19_BASE_URL = 'https://ai2-semanticscholar-cord-19.s3-us-west-2.amazonaws.com/latest/{0}{1}'
_CORD19_METADATA = 'metadata'
_CORD19_SUBSETS = {
    'comm_use_subset',
    'noncomm_use_subset',
    'custom_license',
    'biorxiv_medrxiv',
}

_CORD19_DOWNLOAD_PATH = Path('resources/cord19_data')


class Cord19DataPoint(ArticleDataPoint):
    def __init__(self, raw_data, fulltext):
        super().__init__()
        self.raw_data = raw_data
        self.fulltext = fulltext

    @property
    def doi(self):
        return self.raw_data['doi']

    @property
    def title(self):
        return self.raw_data['title']

    @property
    def abstract(self):
        return self.raw_data['abstract']

    def extract_authors(self):
        return [f"{name},".split(',') for name in self.raw_data['authors'].split(';') if name]

    def extract_content(self):
        return self.fulltext

    def extract_preview_image(self):
        return None

    @property
    def data_source_name(self):
        return DataSource.CORD19_DATASOURCE_NAME

    @property
    def paperhost_name(self):
        paperhost = self.raw_data['source_x']
        if paperhost == 'medrxiv': return 'medRxiv'
        if paperhost == 'biorxiv': return 'bioRxiv'
        return paperhost

    @property
    def paperhost_url(self):
        return None

    @property
    def url(self):
        if self.raw_data['pubmed_id']:
            return f"https://www.ncbi.nlm.nih.gov/pubmed/{self.raw_data['pubmed_id']}/"
        if self.raw_data['pmcid']:
            return f"https://www.ncbi.nlm.nih.gov/pmc/articles/{self.raw_data['pmcid']}/"
        return None

    @property
    def pdf_url(self):
        return self.raw_data['url']

    @property
    def journal(self):
        return self.raw_data['journal']

    @property
    def published_at(self):
        try:
            return datetime.strptime(self.raw_data['publish_time'], '%Y-%m-%d').date()
        except ValueError:
            return None

    @property
    def version(self):
        return None
        # TODO!
        # sha = self.raw_data['sha']
        # if sha:
        #     # TODO: Sometimes, more than one PDF version for one DOI exists.
        #     #  Currently we take just the last one of them.
        #     return sha.split(';')[-1].strip()
        # else:
        #     return None

    @property
    def is_preprint(self):
        return self.raw_data['source_x'] == 'medrxiv' or self.raw_data['source_x'] == 'biorxiv'

    @property
    def pubmed_id(self):
        if self.raw_data['pubmed_id']:
            return self.raw_data['pubmed_id']
        return None

    @property
    def pmcid(self):
        if self.raw_data['pmcid']:
            return self.raw_data['pmcid']
        return None


class Cord19Updater(DataUpdater):
    def __init__(self, log=print):
        super().__init__(log)
        self.cache = Cord19Cache()

    def _count(self):
        return self.cache.size

    def _preprocess(self):
        self.cache.refresh()

    @property
    def _data_source_name(self):
        return DataSource.CORD19_DATASOURCE_NAME

    def _get_data_points(self):
        for raw_data in self.cache.metadata:
            if raw_data['publish_time'] < '2019-12-31':
                continue
            if raw_data['pdf_json_files']:
                fulltext = self.cache.fulltext(raw_data['pdf_json_files'].split()[-1])
            elif raw_data['pmc_json_files']:
                fulltext = self.cache.fulltext(raw_data['pmc_json_files'].split()[-1])
            else:
                fulltext = None
            yield Cord19DataPoint(raw_data=raw_data, fulltext=fulltext)

    def _get_data_point(self, doi):
        try:
            return Cord19DataPoint(next(x for x in self.cache.metadata if x['doi'] == doi))
        except StopIteration:
            return None

    @staticmethod
    def remove_raw_data():
        shutil.rmtree(_CORD19_DOWNLOAD_PATH)
