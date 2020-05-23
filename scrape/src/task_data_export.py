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

    def __init__(self, locally: bool = False, s3: bool = True, *args, **kwargs):
        super(ExportDataTask, self).__init__(*args, **kwargs)
        self.locally = locally
        self.s3 = s3

    def run(self):
        if self.locally:
            out_dir = "resources/dbexport"
        elif self.s3:
            out_dir = "tmp"
        else:
            self.log("Neither S3 nor local export specified. Abort.")
            return

        self.log(
            f"Export {Paper.objects.count()} articles to "
            f"{'S3' if self.s3 else 'local disk'}"
            f"{' and local disk' if self.s3 and self.locally else ''}"
        )

        filename = DataExport.export_data(
            Paper.objects.all(), out_dir=out_dir, log=self.log
        )
        filepath = f"{out_dir}/{filename}"

        if self.locally:
            self.log(f'Store export archive at "{filepath}"')

        if self.s3:
            s3_client = S3BucketClient(
                aws_access_key=settings.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                endpoint_url=settings.AWS_S3_ENDPOINT_URL,
                bucket=settings.AWS_STORAGE_BUCKET_NAME,
            )
            s3_key = f"dbexport/{filename}"
            s3_client.upload(filepath, s3_key)
            self.log(
                "Upload export archive to "
                f"{s3_client.endpoint_url}/{s3_client.bucket}/{s3_key}"
            )

        if not self.locally:
            self.log(f'Remove "{filepath}"')
            os.remove(filepath)
