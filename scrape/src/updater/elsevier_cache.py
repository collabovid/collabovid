import itertools
import json
import os
import pathlib
from datetime import datetime, timedelta
from io import BytesIO
from random import randrange
from time import sleep
from timeit import default_timer as timer
from multiprocessing.pool import ThreadPool
from typing import Any, List, Tuple

import pysftp
#from django.conf import settings

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


def sftp_content_download(filename):
    """Download file content (as string) for all given filenames from Elsevier Covid-19 SFTP server."""
    sleep(30)
    with ElsevierSFTP() as sftp:
        flo = BytesIO()
        sftp.getfo(f'{filename}', flo)
        flo.seek(0)
        content = flo.read().decode("utf-8")
        flo.close()
        return content


def partition(lst, n):
    """
    Partition list into n equal sized chunks.
    Source: https://stackoverflow.com/a/2660034/9519322
    """
    division = len(lst) / n
    return [lst[round(division * i):round(division * (i + 1))] for i in range(n)]


class ElsevierCache:
    __LAST_UPDATE_PATH = 'last_update_timestamp.txt'
    __METADATA_INDEX_FILE = '_index_metadata.txt'

    def __init__(self, path, log=print):
        self.log = log
        self.path = pathlib.Path(path)
        self._metadata = None
        self._metadata_index = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
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
            except FileNotFoundError:
                self.log(f"File not exists: {self.path}/{filename}")
            except json.decoder.JSONDecodeError:
                self.log(f"JSON parse error in {filename}")
            except KeyError:
                self.log(f"Found no DOI in JSON file {filename}")

    def get_metadata(self):
        if not self._metadata:
            self._read_metadata()
        return self._metadata


if __name__ == '__main__':
    start = timer()
    with ElsevierCache(path=f"cache/elsevier") as cache:
        cache.refresh()
        metadata = cache.get_metadata()
    end = timer()
    print(timedelta(seconds=end-start))