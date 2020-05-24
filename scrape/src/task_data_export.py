import os

from collabovid_store.s3_utils import S3BucketClient
from data.models import Paper
from django.conf import settings
from tasks.definitions import register_task, Runnable

from .export_import.data_export import DataExport


@register_task
class ExportDataTask(Runnable):
    @staticmethod
    def task_name():
        return "export-database-records"

    @staticmethod
    def description():
        return (
            "Export all database records to disk or to S3. Topics, topic assignments "
            "and topic scores are excluded."
        )

    def __init__(self, *args, **kwargs):
        super(ExportDataTask, self).__init__(*args, **kwargs)

    def run(self):
        if settings.DB_EXPORT_STORE_LOCALLY:
            self.log(f"Export {Paper.objects.count()} articles locally")
        else:
            self.log(f"Export {Paper.objects.count()} articles to S3")

        out_dir = settings.DB_EXPORT_LOCAL_DIR

        filename = DataExport.export_data(
            Paper.objects.all(), out_dir=out_dir, log=self.log
        )
        filepath = f"{out_dir}/{filename}"

        if not settings.DB_EXPORT_STORE_LOCALLY:
            s3_bucket_client = S3BucketClient(
                aws_access_key=settings.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                endpoint_url=settings.AWS_S3_ENDPOINT_URL,
                bucket=settings.AWS_STORAGE_BUCKET_NAME,
            )
            s3_key = f"{settings.S3_DB_EXPORT_LOCATION}/{filename}"
            s3_bucket_client.upload(filepath, s3_key)
            self.log(
                "Upload export archive to "
                f"{s3_bucket_client.endpoint_url}/{s3_bucket_client.bucket}/{s3_key}"
            )

            self.log(f'Remove "{filepath}"')
            os.remove(filepath)
        else:
            self.log(
                "Store archive at "
                f"{filepath}"
            )