import boto3
import os
from os.path import join, exists
import json
import zipfile
import dateutil.parser

aws_base_dir = os.getenv('AWS_BASE_DIR', '')
models_directory = os.getenv('MODELS_DIRECTORY', '/models')
s3 = boto3.resource(
    service_name='s3',
    aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
    aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
    endpoint_url=os.getenv('S3_HOST'),
)
bucket = os.getenv('BUCKET', 'test')


def upload_file(path, key):
    object = s3.Object(bucket, key)
    with open(path, 'r') as f:
        object.put(Body=f.read())


def download_file(key, local_filename):
    s3.Bucket(bucket).download_file(key, local_filename)


def sync_sentence_transformer_model():
    if not exists(join(models_directory, 'sentence_transformer')):
        print('Downloading Sentence Transformer model')
        local_download_path = join(models_directory, 'sentence-transformer.zip')
        download_file(join(aws_base_dir, 'sentence-transformer.zip'), local_download_path)
        print("Extracting Sentence Transformer model")
        with zipfile.ZipFile(local_download_path, 'r') as zip_ref:
            zip_ref.extractall(models_directory)


def sync_lda_model():
    if not exists(join(models_directory, 'lda')):
        print("Downloading lda")
        local_download_path = join(models_directory, 'lda.zip')
        download_file(join(aws_base_dir, 'lda.zip'), local_download_path)
        print("Extracting lda")
        with zipfile.ZipFile(local_download_path, 'r') as zip_ref:
            zip_ref.extractall(models_directory)


def sync_paper_matrix():
    file_content = s3.Object(bucket, 'paper_matrix.json').get()['Body'].read().decode('utf-8')
    timestamps_remote = json.loads(file_content)
    local_timestamp_path = join(models_directory, 'paper_matrix.json')
    if not exists(local_timestamp_path):
        timestamps_local = {}
    else:
        with open(local_timestamp_path, 'r') as f:
            timestamps_local = json.load(f)
    for key, timestamp in timestamps_remote.items():
        if not key in timestamps_local or dateutil.parser.parse(timestamps_local[key]) < dateutil.parser.parse(
                timestamp):
            download_file(join(aws_base_dir, 'paper_matrix_' + key + '.pkl'),
                          join(models_directory, 'paper_matrix_' + key + '.pkl'))
    with open(local_timestamp_path, 'w') as f:
        json.dump(timestamps_remote, f)


if __name__ == '__main__':
    print("Sync Starting")
    print("Syncing sentence transformer model")
    sync_sentence_transformer_model()
    print("Syncing lda model")
    sync_lda_model()
    print("Syncing paper matrix")
    sync_paper_matrix()
