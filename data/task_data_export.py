from data.data_export import DataExporter
from data.models import Paper
from tasks.definitions import Runnable


class ExportDataTask(Runnable):
    def task_name(self):
        return "export-database-records"

    def __init__(self, *args, **kwargs):
        super(ExportDataTask, self).__init__(*args, **kwargs)

    def run(self):
        exporter = DataExporter()
        path = exporter.export_data(Paper.objects.all(), output_directory='resources')

        # Upload .tar.gz archive to S3 bucket (expriable object and public?) and write link to log
