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
from data.models import DataSource
from scrape.updater.data_updater import DataUpdater, ArticleDataPoint


_CORD19_DATA_PRIORITY = 10
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
    def __init__(self, raw_data, log=print):
        super().__init__()
        self.raw_data = raw_data
        self.log = log

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

    def _get_json_path(self):
        path = Path(_CORD19_DOWNLOAD_PATH) / self.raw_data['full_text_file']

        if self.raw_data['has_pdf_parse']:
            path /= 'pdf_json'
        elif self.raw_data['has_pmc_xml_parse']:
            path /= 'pmc_json'
        else:
            return None

        path /= f"{self.raw_data['sha']}.json"

        if os.path.exists(path):
            return path
        else:
            return None

    def extract_content(self):
        json_path = self._get_json_path()
        if json_path and os.path.exists(json_path):
            with json_path.open('r') as file:
                return '\n'.join([paragraph['text'] for paragraph in json.load(file)['body_text']])

    @property
    def data_source_name(self):
        return DataSource.CORD19_DATASOURCE_NAME

    @property
    def data_source_priority(self):
        return _CORD19_DATA_PRIORITY

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
        if self.raw_data['url'].endswith('.pdf'):
            return self.raw_data['url']
        return None

    @property
    def journal(self):
        return self.raw_data['journal']

    @property
    def published_at(self):
        try:
            date = datetime.strptime(self.raw_data['publish_time'], '%Y-%m-%d').date()
            # if date >= datetime.now() + timedelta(days=7):
            #     # Return None, if publishing date is more than one wekk in the future
            #     return None
            return date
        except ValueError:
            return None

    @property
    def version(self):
        sha = self.raw_data['sha']
        if sha:
            # TODO: Sometimes, more than one PDF version for one DOI exists.
            #  Currently we take just the last one of them.
            return sha.split(';')[-1].strip()
        else:
            return None

    @property
    def is_preprint(self):
        return self.raw_data['source_x'] == 'medrxiv' or self.raw_data['source_x'] == 'biorxiv'


class Cord19Updater(DataUpdater):
    def __init__(self, log=print):
        super().__init__(log)
        self.metadata = None

    def _download_metadata(self):
        """Downloads the metadata CSV file."""
        self.log("Download latest CORD19 meta data. This may take a few minutes.")
        url = _CORD19_BASE_URL.format(_CORD19_METADATA, '.csv')
        download = requests.get(url)
        decoded_content = download.content.decode('utf-8')

        lines = decoded_content.splitlines()
        header = lines[0].split(',')
        reader = csv.reader(lines[1:], delimiter=',')

        self.metadata = [{k: v for (k, v) in zip(header, row)} for row in reader]

    def _download_full_text_data(self):
        """Downloads the full text of all CORD19 articles."""
        self.log("Download latest CORD19 full text data. This may take a few (more) minutes.")

        # Remove data directory with old content first
        if os.path.exists(_CORD19_DOWNLOAD_PATH):
            shutil.rmtree(_CORD19_DOWNLOAD_PATH)
        os.makedirs(_CORD19_DOWNLOAD_PATH, exist_ok=True)

        for subset_suffix in _CORD19_SUBSETS:
            print(f"- {subset_suffix}")
            url = _CORD19_BASE_URL.format(subset_suffix, '.tar.gz')
            targz_path = _CORD19_DOWNLOAD_PATH / 'tmp.tar.gz'

            with requests.get(url, stream=True) as download_stream:
                with open(targz_path, 'wb') as file:
                    shutil.copyfileobj(download_stream.raw, file)

            tar = tarfile.open(targz_path, 'r:gz')
            tar.extractall(path=_CORD19_DOWNLOAD_PATH)
            tar.close()
            os.remove(targz_path)

    def _download_data(self):
        if not self.metadata:
            start = timer()
            self._download_metadata()
            end = timer()
            self.log(f"Finished downloading meta data: {timedelta(seconds=end - start)}")
            start = timer()
            #self._download_full_text_data()
            end = timer()
            self.log(f"Finished downloading full text data: {timedelta(seconds=end - start)}")

    def _count(self):
        self._download_data()
        return len(self.metadata)

    @property
    def _data_source_name(self):
        return DataSource.CORD19_DATASOURCE_NAME

    def _get_data_points(self):
        self._download_data()
        for raw_data in self.metadata:
            yield Cord19DataPoint(raw_data=raw_data)

    def _get_data_point(self, doi):
        self._download_metadata()
        try:
            return Cord19DataPoint(next(x for x in self.metadata if x['doi'] == doi))
        except StopIteration:
            return None

    @staticmethod
    def remove_raw_data():
        shutil.rmtree(_CORD19_DOWNLOAD_PATH)
