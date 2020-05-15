from collabovid_store.s3_utils import S3BucketClient
from os.path import join, exists
import botocore
from typing import List
import datetime
import os
import json
import dateutil.parser
import zipfile
import shutil


def current_timestamp():
    return str(datetime.datetime.utcnow().replace(microsecond=0))


def refresh_local_timestamps(local_directory, keys, timestamp_file_name='timestamps.json'):
    timestamp_file_path = join(local_directory, timestamp_file_name)
    if not exists(timestamp_file_path):
        timestamp_data = {}
    else:
        with open(timestamp_file_path, 'r') as f:
            timestamp_data = json.load(f)

    for key in keys:
        timestamp_data[key] = current_timestamp()


class SyncableStore:
    def __init__(self, remote_root_path: str, s3_bucket_client: S3BucketClient, timestamp_file_name='timestamps.json'):

        self.s3_bucket_client = s3_bucket_client
        self.timestamp_file_name = timestamp_file_name

        self.remote_root_path = remote_root_path
        self.remote_timestamp_file_path = join(remote_root_path, timestamp_file_name)

    def sync_to_local_directory(self, local_root_path: str, verbose=True):
        local_root_path = local_root_path
        local_timestamp_file_path = join(local_root_path, self.timestamp_file_name)

        os.makedirs(local_root_path, exist_ok=True)

        # Download remote timestamps
        timestamps_remote = self._get_remote_timestamps(verbose=verbose)

        # Loading local timestamps file if present
        if not exists(local_timestamp_file_path):
            timestamps_local = {}
        else:
            with open(local_timestamp_file_path, 'r') as f:
                timestamps_local = json.load(f)

        # Download new files if remote timestamp is older than local timestamp
        for key, timestamp in timestamps_remote.items():
            if key not in timestamps_local or dateutil.parser.parse(timestamps_local[key]) < dateutil.parser.parse(
                    timestamp):
                if verbose:
                    print("Refreshing: " + key)
                local_file_path = join(local_root_path, key)
                self.s3_bucket_client.download_file(join(self.remote_root_path, key), local_file_path)
                self._post_file_download(local_root_path, key)

        # Write new timestamps file
        with open(local_timestamp_file_path, 'w') as f:
            json.dump(timestamps_remote, f)

    def update_remote(self, directory_path: str, keys: List[str], verbose=True):
        timestamp_data = self._get_remote_timestamps(verbose=verbose)

        for key in keys:
            if verbose:
                print("Uploading: " + key)
            self._pre_file_upload(directory_path, key)
            file_name = key
            path = join(directory_path, file_name)
            self.s3_bucket_client.upload(path, join(self.remote_root_path, file_name))
            timestamp_data[key] = current_timestamp()
            self._post_file_upload(directory_path, key)
        self.s3_bucket_client.upload_as_json(self.remote_timestamp_file_path, timestamp_data)

    def _get_remote_timestamps(self, verbose=True):
        # Downloading remote timestamps json file
        try:
            timestamp_data = self.s3_bucket_client.get_json(self.remote_timestamp_file_path)
        except botocore.exceptions.ClientError as e:
            if e.response['Error']['Code'] == "NoSuchKey":
                # The object does not exist.
                if verbose:
                    print("No remote timestamp file found. Creating new one...")
                timestamp_data = {}
            else:
                # Something else has gone wrong.
                print("Unknown error while retrieving remote timestamp file.")
                print(e.response)
                raise e
        return timestamp_data

    def _post_file_download(self, directory, file_name):
        pass

    def _pre_file_upload(self, directory, file_name):
        pass

    def _post_file_upload(self, directory, file_name):
        pass


class PaperMatrixStore(SyncableStore):
    def __init__(self, s3_bucket_client: S3BucketClient, remote_root_path='models/paper_matrix'):
        super().__init__(remote_root_path=remote_root_path, s3_bucket_client=s3_bucket_client)

    def sync(self):
        self.sync_to_local_directory('/models/paper_matrix')

    def update_remote(self, directory_path: str, keys: List[str], verbose=True):
        super().update_remote(directory_path=directory_path, keys=[f'{key}.pkl' for key in keys])


class ModelsStore(SyncableStore):
    def __init__(self, s3_bucket_client: S3BucketClient, remote_root_path='models'):
        super().__init__(remote_root_path=remote_root_path, s3_bucket_client=s3_bucket_client)

    def sync(self):
        self.sync_to_local_directory('/models')

    def _post_file_download(self, directory, file_name):
        file_path = join(directory, file_name)

        # Extracting in models folder
        with zipfile.ZipFile(file_path, 'r') as zip_ref:
            zip_ref.extractall(join(directory, file_name.replace('.zip', '')))
        os.remove(file_path)

    def _pre_file_upload(self, directory, file_name):
        model_directory = join(directory, file_name.replace('.zip', ''))
        shutil.make_archive(model_directory, 'zip', model_directory)

    def _post_file_upload(self, directory, file_name):
        os.remove(join(directory, file_name))

    def update_remote(self, directory_path: str, keys: List[str], verbose=True):
        super().update_remote(directory_path=directory_path, keys=[f'{key}.zip' for key in keys])
