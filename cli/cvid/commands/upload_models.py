from .command import Command
from os.path import join
import os
import shutil
import boto3
import datetime
import botocore
import json
from boto3.s3.transfer import TransferConfig

paper_matrices = [
    'lda',
    'title_sentence_vectorizer'
]


def current_timestamp():
    return str(datetime.datetime.utcnow().replace(microsecond=0))


class S3Store():
    def __init__(self, aws_access_key, aws_secret_access_key, endpoint_url, bucket):
        self.s3 = boto3.resource(
            service_name='s3',
            aws_access_key_id=aws_access_key,
            aws_secret_access_key=aws_secret_access_key,
            endpoint_url=endpoint_url,
        )
        self.bucket = bucket

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


def zip_model_and_upload(models_directory, dirname, s3_store: S3Store, base_remote_path='models'):
    dir_path = join(models_directory, dirname)
    zip_path = join(models_directory, '{}.zip'.format(dir_path))
    print("\tzipping directory")
    shutil.make_archive(dir_path, 'zip', dir_path)
    remote_key = join(base_remote_path, '{}.zip'.format(dirname))
    print("\tuploading zip file")
    s3_store.upload(local_file=zip_path, remote_key=remote_key)
    os.remove(zip_path)
    print("\tDone")


def upload_paper_matrices(models_directory, s3_store: S3Store, paper_matrix_keys, base_remote_path='models'):
    remote_paper_matrix_dir_path = join(base_remote_path, 'paper_matrix')
    remote_timestamp_file_path = join(remote_paper_matrix_dir_path, 'paper_matrix.json')
    local_paper_matrix_dir_path = join(models_directory, 'paper_matrix')
    paper_matrix_file_extension = '.pkl'

    try:
        timestamp_data = s3_store.get_json(remote_timestamp_file_path)
    except botocore.exceptions.ClientError as e:
        if e.response['Error']['Code'] == "NoSuchKey":
            # The object does not exist.
            print('No remote timestamps file found')
            print("\tNo remote timestamp file found. Creating new one...")
            timestamp_data = {}
        else:
            # Something else has gone wrong.
            print("Unknown error while retrieving remote timestamp file.")
            print(e.response)
            return

    for paper_matrix_key in paper_matrix_keys:
        print("\tUploading Paper matrix: " + paper_matrix_key)
        file_name = paper_matrix_key + paper_matrix_file_extension
        path = join(local_paper_matrix_dir_path, file_name)
        s3_store.upload(path, join(remote_paper_matrix_dir_path, file_name))
        timestamp_data[paper_matrix_key] = current_timestamp()
    s3_store.upload_as_json(remote_timestamp_file_path, timestamp_data)


class UploadModelsCommand(Command):
    def run(self, args):
        models_directory = join(os.getcwd(), args.directory)
        aws_access_key = self.current_env_config()['s3_access_key']
        aws_secret_access_key = self.current_env_config()['s3_secret_access_key']
        endpoint_url = self.current_env_config()['s3_endpoint_url']
        bucket = self.current_env_config()['s3_bucket_name']
        s3_store = S3Store(aws_access_key=aws_access_key, aws_secret_access_key=aws_secret_access_key,
                           endpoint_url=endpoint_url, bucket=bucket)
        if args.models is not None:
            for model in args.models:
                self.print_info('Processing {}'.format(model))
                zip_model_and_upload(models_directory=models_directory, dirname=model, s3_store=s3_store)

        if args.paper_matrices is not None:
            self.print_info('Processing Paper Matrices')
            upload_paper_matrices(models_directory=models_directory, s3_store=s3_store,
                                  paper_matrix_keys=args.paper_matrices)

    def add_arguments(self, parser):
        parser.add_argument('-d', '--directory', help="Models directory", default='models')
        parser.add_argument('-m', '--models', nargs='*', choices=['lda', 'sentence_transformer'])
        parser.add_argument('-p', '--paper-matrices', nargs='*', choices=paper_matrices)

    def help(self):
        return "Upload models to s3"

    def name(self):
        return "upload-models"
