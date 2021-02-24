import json

import boto3
from boto3.s3.transfer import TransferConfig
from urllib.parse import unquote as urlunquote


class S3BucketClient:
    def __init__(self, aws_access_key, aws_secret_access_key, endpoint_url, bucket):
        self.s3 = boto3.resource(
            service_name="s3",
            aws_access_key_id=aws_access_key,
            aws_secret_access_key=aws_secret_access_key,
            endpoint_url=endpoint_url,
        )
        self.bucket = bucket
        self.endpoint_url = endpoint_url

    def upload(self, local_file, remote_key):
        config = TransferConfig()
        self.s3.meta.client.upload_file(
            local_file, self.bucket, remote_key, Config=config
        )

    def download_file(self, key, local_filename):
        self.s3.Bucket(self.bucket).download_file(key, local_filename)

    def delete_file(self, key):
        self.s3.Object(self.bucket, key).delete()

    def get_json(self, key):
        object = self.s3.Object(self.bucket, key).get()
        file_content = object["Body"].read().decode("utf-8")
        return json.loads(file_content)

    def upload_as_json(self, key, data):
        object = self.s3.Object(self.bucket, key)
        object.put(Body=str.encode(json.dumps(data)))

    def make_public(self, key):
        object_acl = self.s3.ObjectAcl(self.bucket, key)
        response = object_acl.put(ACL='public-read')
        return response

    def all_objects(self, prefix=""):
        return [
            urlunquote(e["Key"])
            for p in self.s3.meta.client.get_paginator("list_objects_v2").paginate(
                Bucket=self.bucket, Prefix=prefix
            ) if "Contents" in p
            for e in p["Contents"]
        ]
