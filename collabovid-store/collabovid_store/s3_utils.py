from boto3.s3.transfer import TransferConfig
import boto3
import json


class S3BucketClient():
    def __init__(self, aws_access_key, aws_secret_access_key, endpoint_url, bucket):
        self.s3 = boto3.resource(
            service_name='s3',
            aws_access_key_id=aws_access_key,
            aws_secret_access_key=aws_secret_access_key,
            endpoint_url=endpoint_url,
        )
        self.bucket = bucket
        self.endpoint_url = endpoint_url

    def upload(self, local_file, remote_key):
        config = TransferConfig(multipart_threshold=(1024 ** 3) * 2)
        self.s3.meta.client.upload_file(local_file, self.bucket, remote_key,
                                        Config=config)

    def download_file(self, key, local_filename):
        self.s3.Bucket(self.bucket).download_file(key, local_filename)

    def get_json(self, key):
        object = self.s3.Object(self.bucket, key).get()
        file_content = object['Body'].read().decode('utf-8')
        return json.loads(file_content)

    def upload_as_json(self, key, data):
        object = self.s3.Object(self.bucket, key)
        object.put(Body=str.encode(json.dumps(data)))
