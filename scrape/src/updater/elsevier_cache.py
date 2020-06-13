import json
import os
import pathlib
from datetime import datetime
from io import BytesIO
from random import randrange
from time import sleep
from multiprocessing.pool import ThreadPool
from typing import List, Tuple

import pysftp

ELSEVIER_SFTP_HOST = "coronacontent.np.elsst.com"
ELSEVIER_SFTP_USERNAME = "public"
ELSEVIER_SFTP_PASSWORD = "beat_corona"


class ElsevierSFTP(pysftp.Connection):
    def __init__(self):
        cnopts = pysftp.CnOpts()
        cnopts.hostkeys = None  # No SSH key verification
        super().__init__(
            host=ELSEVIER_SFTP_HOST,
            username=ELSEVIER_SFTP_USERNAME,
            password=ELSEVIER_SFTP_PASSWORD,
            cnopts=cnopts,
        )


def sftp_download(args: Tuple[List[str], str]):
    sleep(randrange(0, 120))  # Avoid starting all connections simultaneously
    rel_paths, out_dir = args
    with ElsevierSFTP() as sftp:
        for rel_path in rel_paths:
            local_path = f"{out_dir}/{rel_path}"
            os.makedirs(os.path.dirname(local_path), exist_ok=True)
            sftp.get(rel_path, local_path)


def sftp_content_download(filename, do_sleep=True, decode=True):
    """Download file content (as string or bytes) for given filename from Elsevier Covid-19 SFTP server."""
    if do_sleep:
        sleep(30)
    with ElsevierSFTP() as sftp:
        flo = BytesIO()
        sftp.getfo(f'{filename}', flo)
        flo.seek(0)
        content = flo.read()
        flo.close()
        return content.decode('utf-8') if decode else content


def partition(lst, n):
    """
    Partition list into n equal sized chunks.
    Source: https://stackoverflow.com/a/2660034/9519322
    """
    division = len(lst) / n
    return [lst[round(division * i):round(division * (i + 1))] for i in range(n)]


class DoiPiiMapping:
    """Stores a mapping from DOIs to PIIs as Dict. Reads and saves the mapping in a persistent file."""
    def __init__(self, path):
        self._mapping = None
        self.path = pathlib.Path(path)
        if os.path.isfile(self.path):
            with open(self.path, 'r') as f:
                self._mapping = json.load(f)
        else:
            self._mapping = {}

    @staticmethod
    def clean_pii(pii):
        """
        Remove all non-alphanum. characters from PII.
        Needed because that's the way files are named on Elsevier's side
        """
        return ''.join([c for c in pii if c.isalnum()])

    def add(self, doi, pii):
        cleaned_pii = DoiPiiMapping.clean_pii(pii)
        if doi not in self._mapping:
            self._mapping[doi] = cleaned_pii

    def get(self, doi):
        return self._mapping[doi] if doi in self._mapping else None

    def save(self):
        with open(self.path, 'w') as f:
            json.dump(self._mapping, f, indent=4)


class ElsevierCache:
    __LAST_UPDATE_PATH = 'last_update_timestamp.txt'
    __METADATA_INDEX_FILE = '_index_metadata.txt'
    __DOI_PII_MAPPING_FILE = 'doi_pii_mapping.txt'

    def __init__(self, path, log=print):
        self.log = log
        self.path = pathlib.Path(path)
        self._metadata = None
        self._metadata_index = None
        self._doi_pii_mapping = DoiPiiMapping(self.path / self.__DOI_PII_MAPPING_FILE)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._doi_pii_mapping.save()
        return

    @staticmethod
    def latest_version():
        return datetime.strptime(
            sftp_content_download("timestamp_of_last_update.txt"),
            "%Y-%m-%dT%H:%M:%SZ",
        )

    def cache_version(self):
        path = self.path / self.__LAST_UPDATE_PATH
        if not os.path.isfile(path):
            return None
        else:
            with open(path, "r") as file:
                return datetime.strptime(
                    file.read(),
                    "%Y-%m-%d %H:%M:%S"
                )

    def refresh(self):
        self.log("Check latest elsevier dataset version against cache version")
        cache_version = self.cache_version()
        latest_version = self.latest_version()
        self.log(f"Cache version: {cache_version}, latest version: {latest_version}")
        if not cache_version or cache_version < latest_version:
            self.log("Elsevier dataset is newer than cache version, update data")
            new_metadata_index = self._get_remote_metadata_index()
            old_metadata_index = self._get_cache_metadata_index()

            updated_files = []

            for file, date in new_metadata_index.items():
                if (file not in old_metadata_index
                        or date > old_metadata_index[file]
                        or not os.path.isfile(self.path / file)
                ):
                    updated_files.append(file)

            self.log(f"Download {len(updated_files)} new/updated metadata files")

            if len(updated_files) > 0:
                 self.log("Download metadata files. This may take some minutes")
                 poolsize = 10
                 filename_chunks = partition(updated_files, poolsize)
                 with ThreadPool(poolsize) as pool:
                     pool.map(sftp_download, [(chunk, self.path) for chunk in filename_chunks])

            for file in updated_files:
                if os.path.isfile(self.path / file):
                    old_metadata_index[file] = new_metadata_index[file]

            with open(self.path / self.__METADATA_INDEX_FILE, "w") as metadata_index_file:
                # metadata_index_file.writelines([f"{file} {date}" for file, date in old_metadata_index.items()])
                json.dump(old_metadata_index, metadata_index_file, indent=4)

            with open(self.path / self.__LAST_UPDATE_PATH, "w") as last_update_file:
                 last_update_file.write(datetime.strftime(latest_version, "%Y-%m-%d %H:%M:%S"))

        self.log("Cache is up-to-date")

    def _get_remote_metadata_index(self):
        self.log("Download remote metadata index file")
        filecontent = sftp_content_download("_index_meta.txt")
        if filecontent:
            lines = filecontent.splitlines()[1:] # Skip header line
            metadata_index = {}
            for line in lines:
                split = line.split(",")
                file = split[0].strip()
                date = int(datetime.strftime(datetime.strptime(split[1].strip(), "%Y-%m-%d %H:%M:%S+00:00"), "%s"))
                metadata_index[file] = date
            return metadata_index
        else:
            raise Exception("Failed to download metadata index")

    def _get_cache_metadata_index(self):
        if not self._metadata_index:
            self.log("Read cached meta data index file")
            path = self.path / self.__METADATA_INDEX_FILE
            self._metadata_index = {}
            try:
                with open(path, "r") as file:
                    self._metadata_index = json.load(file)
            except FileNotFoundError:
                pass
        return self._metadata_index

    def _read_metadata(self):
        metadata_index = self._get_cache_metadata_index()
        self._metadata = {}

        for filename, date in metadata_index.items():
            try:
                with open(f"{self.path}/{filename}", "r") as file:
                    content = json.load(file)["full-text-retrieval-response"]
                    content["last_updated"] = date
                    doi = content["coredata"]["prism:doi"].strip()
                    self._metadata[doi] = content

                    pii = content["coredata"]["pii"]
                    self._doi_pii_mapping.add(doi, pii)
            except FileNotFoundError:
                self.log(f"File not exists: {self.path}/{filename}")
            except json.decoder.JSONDecodeError:
                self.log(f"JSON parse error in {filename}")
            except KeyError:
                self.log(f"Found no DOI in JSON file {filename}")

        self._doi_pii_mapping.save()

    def get_metadata(self):
        if not self._metadata:
            self._read_metadata()
        return self._metadata

    def get_pdf(self, doi):
        """Retrieves the PDF file for the given DOI from the Elsevier server."""
        pii = self._doi_pii_mapping.get(doi)
        if not pii:
            self.log(f"No PII found for DOI {doi}")
            return None
        try:
            return sftp_content_download(f"pdf/{pii}.pdf", do_sleep=False, decode=False)
        except FileNotFoundError:
            self.log(f"PDF for doi {doi} (pii {pii}) does not exist on server.")
            return None
