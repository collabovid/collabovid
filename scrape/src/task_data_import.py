import os

from collabovid_store.s3_utils import S3BucketClient
from django.conf import settings
from tasks.definitions import register_task, Runnable

from src.export_import.data_import import DataImport
from tasks.colors import *


@register_task
class ImportDataTask(Runnable):
    @staticmethod
    def task_name():
        return "import-database-records"

    @staticmethod
    def description():
        return (
            "Import database records from S3 bucket. Topics, topic assignments "
            "and topic scores are excluded."
        )

    def __init__(self, filename: str, *args, **kwargs):
        super(ImportDataTask, self).__init__(*args, **kwargs)
        self.filename = filename

    def run(self):
        if not self.filename:
            self.log("S3 URL needs to be specified. Abort.")

        local_dir = settings.DB_EXPORT_LOCAL_DIR
        local_filepath = f"{local_dir}/{self.filename}"

        data_importer = DataImport(log=self.log, progress=self.progress)

        if not settings.DB_EXPORT_STORE_LOCALLY:
            if not os.path.exists(local_dir):
                self.log(f"Create directory \"{local_dir}\"")
                os.makedirs(local_dir)

            s3_client = S3BucketClient(
                aws_access_key=settings.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                endpoint_url=settings.AWS_S3_ENDPOINT_URL,
                bucket=settings.AWS_STORAGE_BUCKET_NAME,
            )

            try:
                s3_key = f"{settings.S3_DB_EXPORT_LOCATION}/{self.filename}"
                self.log(f"Download S3 key \"{s3_key}\" to \"{local_filepath}\"")
                s3_client.download_file(s3_key, local_filepath)

                self.log(f"Import data from \"{local_filepath}\"")
                data_importer.import_data(local_filepath)
            finally:
                if os.path.exists(local_filepath):
                    self.log(f"Remove \"{local_filepath}\"")
                    os.remove(local_filepath)
        else:
            self.log(f"Import data from \"{local_filepath}\"")
            data_importer.import_data(local_filepath)