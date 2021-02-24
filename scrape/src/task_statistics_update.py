from tasks.definitions import register_task, Runnable
from data.models import Paper
from collabovid_statistics import PaperStatistics
import json
from collabovid_store.s3_utils import S3BucketClient
from django.conf import settings


@register_task
class StatisticsUpdateTask(Runnable):

    @staticmethod
    def task_name():
        return "update-statistics"

    def __init__(self, *args, **kwargs):
        super(StatisticsUpdateTask, self).__init__(*args, **kwargs)
        pass

    def run(self):
        statistics = PaperStatistics(Paper.objects)
        result = {'published_at_data': json.loads(statistics.published_at_data),
                  'paper_host_data': json.loads(statistics.paper_host_data)}

        aws_access_key = settings.AWS_ACCESS_KEY_ID
        aws_secret_access_key = settings.AWS_SECRET_ACCESS_KEY
        bucket = settings.AWS_STORAGE_BUCKET_NAME
        endpoint_url = settings.AWS_S3_ENDPOINT_URL
        s3_bucket_client = S3BucketClient(aws_access_key=aws_access_key,
                                          aws_secret_access_key=aws_secret_access_key,
                                          endpoint_url=endpoint_url, bucket=bucket)
        key = 'statistics/statistics.json'
        s3_bucket_client.upload_as_json(key, result)
        response = s3_bucket_client.make_public(key)
        print(response)
