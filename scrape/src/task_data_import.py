import os

from collabovid_store.s3_utils import S3BucketClient
from django.conf import settings
from tasks.definitions import register_task, Runnable

from src.export_import.data_import import DataImport


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

    def __init__(self, s3_key: str, *args, **kwargs):
        super(ImportDataTask, self).__init__(*args, **kwargs)
        self.s3_key = s3_key

    def run(self):
        if not self.s3_key:
            self.log("S3 URL needs to be specified. Abort.")

        s3_client = S3BucketClient(
            aws_access_key=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            endpoint_url=settings.AWS_S3_ENDPOINT_URL,
            bucket=settings.AWS_STORAGE_BUCKET_NAME,
        )

        local_dir = "tmp"
        local_filepath = f"{local_dir}/{os.path.basename(self.s3_key)}"

        if not os.path.exists(local_dir):
            self.log(f"Create directory \"{local_dir}\"")
            os.makedirs(local_dir)

        try:
            self.log(f"Download S3 key \"{self.s3_key}\" to \"{local_filepath}\"")
            s3_client.download_file(self.s3_key, local_filepath)

            self.log(f"Import data from \"{local_filepath}\"")
            DataImport.import_data(local_filepath, log=self.log)
        finally:
            if os.path.exists(local_filepath):
                self.log(f"Remove \"{local_filepath}\"")
                os.remove(local_filepath)
