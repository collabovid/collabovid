import csv
import json
import os
import pathlib
import shutil
import tarfile
from datetime import datetime

import requests

from scrape.updater.update_error import UpdateError


class Cord19CacheError(UpdateError):
    pass


class Cord19Cache:
    __CHANGELOG_PATH = 'changelog.txt'
    __METADATA_PATH = 'metadata.csv'
    __FULLTEXT_PATH = 'document_parses/{0}_json/{1}.json'
    __CORD19_BASE_URL = 'https://ai2-semanticscholar-cord-19.s3-us-west-2.amazonaws.com/latest/{0}'

    def __init__(self, path='resources/cache/cord-19', log=print):
        self._path = pathlib.Path(path)
        self._log = log
        self._metadata = None
        self._doimapping = None

    @property
    def size(self):
        return len(self.metadata)

    @property
    def metadata(self):
        if not self._metadata:
            self.__open_metadata_file()
        return self._metadata

    def fulltext(self, relative_path=None, doi=None):
        if not self.cache_version():
            raise Cord19CacheError("Cache is empty")
        if doi:
            if not self._metadata:
                self.__open_metadata_file()
            try:
                pmc_fulltext_path = self._doimapping[doi]['pmc_json_files'].split(';')[0]
                pdf_fulltext_path = self._doimapping[doi]['pdf_json_files'].split(';')[0]
                if pmc_fulltext_path:
                    relative_path = pmc_fulltext_path
                elif pdf_fulltext_path:
                    relative_path = pdf_fulltext_path
                else:
                    return None
            except KeyError:
                raise Cord19CacheError(f"Article with DOI {doi} is not available in current CORD-19 version")

        if relative_path:
            try:
                with open(self._path / relative_path) as file:
                    data = json.loads(file.read())
                    return '\n'.join([x['text'] for x in data['body_text']])
            except IOError as ex:
                raise Cord19CacheError(ex)
        else:
            return None

    def refresh(self):
        self._log("Check latest CORD-19 version with current cache version")
        cache_version = self.cache_version()
        latest_version = self.latest_version()
        if not cache_version or cache_version < latest_version:
            self._log(f"Found no or obsolete cache in {self._path}, load latest CORD-19 dataset")
            self.clear()
            self._metadata = None
            os.makedirs(self._path, exist_ok=True)
            self._log("Download meta data")
            self.__download_metadata()
            self._log("Download fulltext data")
            self.__download_fulltext()
            self._log("Write version file")
            with open(self._path / self.__CHANGELOG_PATH, 'w') as file:
                file.write(latest_version.strftime('%Y-%m-%d'))
            self.__open_metadata_file()
        self._log("CORD-19 cache is up-to-date")

    def clear(self):
        if os.path.exists(self._path):
            shutil.rmtree(self._path)

    def cache_version(self):
        """Checks whether the cache directory and the version file exist and return the version date from the file."""
        file_path = self._path / self.__CHANGELOG_PATH
        if not os.path.isfile(file_path):
            return None
        else:
            with open(file_path, 'r') as file:
                try:
                    content = file.read()
                    return datetime.strptime(content, '%Y-%m-%d').date()
                except ValueError:
                    raise Cord19CacheError(f"Couldn't extract date from version file: {content}")

    @staticmethod
    def latest_version():
        """Downloads the changelog from emantic Scholar and returns the date of the last change record."""
        changelog_url = 'https://ai2-semanticscholar-cord-19.s3-us-west-2.amazonaws.com/latest/changelog'
        try:
            response = requests.get(changelog_url)
        except requests.exceptions.RequestException as ex:
            raise Cord19CacheError(f"Couldn't retrieve newest changelog: {ex}")

        if response.status_code != 200:
            raise Cord19CacheError(f"Couldn't retrieve newest changelog: Status code {response.status_code}")

        first_line = response.text.split('\n', 1)[0].strip()
        try:
            return datetime.strptime(first_line, '%Y-%m-%d').date()
        except ValueError:
            raise Cord19CacheError(f"Couldn't extract date from first line of changelog: {first_line}")

    def __open_metadata_file(self):
        if not self.cache_version():
            raise Cord19CacheError("Cache is empty")
        with open(self._path / self.__METADATA_PATH, 'r') as file:
            lines = file.readlines()
            header = [x.strip() for x in lines[0].split(',')]
            reader = csv.reader(lines[1:], delimiter=',')

            self._metadata = [{k: v for (k, v) in zip(header, row)} for row in reader]
            self._doimapping = {data['doi']: data for data in self._metadata if data['doi']}

    def __download_metadata(self):
        url = self.__CORD19_BASE_URL.format('metadata.csv')

        try:
            response = requests.get(url)
        except requests.exceptions.RequestException as ex:
            raise Cord19CacheError(f"Couldn't retrieve metadata.csv: {ex}")

        if response.status_code != 200:
            raise Cord19CacheError(f"Couldn't retrieve metadata.csv: Status code {response.status_code}")

        decoded_content = response.content.decode('utf-8')
        with open(self._path / self.__METADATA_PATH, 'w') as file:
            file.write(decoded_content)

    def __download_fulltext(self):
        url = self.__CORD19_BASE_URL.format('document_parses.tar.gz')
        targz_path = self._path / 'tmp.tar.gz'
        try:
            with requests.get(url, stream=True) as download_stream:
                with open(targz_path, 'wb') as file:
                    shutil.copyfileobj(download_stream.raw, file)
        except requests.exceptions.RequestException as ex:
            raise Cord19CacheError(f"Couldn't retrieve document_parses.tar.gz: {ex}")

        tar = tarfile.open(targz_path, 'r:gz')
        tar.extractall(path=self._path)
        tar.close()
        os.remove(targz_path)

