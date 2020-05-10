import boto3
import os
from os.path import join, exists
import json
import zipfile
import dateutil.parser
import botocore

aws_base_dir = os.getenv('AWS_BASE_DIR', 'models')
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


def sync_zipped_model(model_name):
    if not exists(join(models_directory, model_name)):
        # Downloading zipped model
        print('\tDownloading {}'.format(model_name))
        zip_file_name = '{}.zip'.format(model_name)
        local_download_path = join(models_directory, zip_file_name)
        print('\tremote path: {}'.format(join(aws_base_dir, zip_file_name)))
        download_file(join(aws_base_dir, zip_file_name), local_download_path)

        # Extracting in models folder
        print("\tExtracting {}".format(local_download_path))
        with zipfile.ZipFile(local_download_path, 'r') as zip_ref:
            zip_ref.extractall(join(models_directory, model_name))
        os.remove(local_download_path)


def sync_paper_matrix():
    timestamp_file_name = 'paper_matrix.json'
    local_paper_matrix_dir_path = join(models_directory, 'paper_matrix')
    remote_paper_matrix_dir_path = join(aws_base_dir, 'paper_matrix')
    remote_timestamp_file_path = join(remote_paper_matrix_dir_path, timestamp_file_name)
    paper_matrix_file_extension = '.pkl'

    os.makedirs(local_paper_matrix_dir_path, exist_ok=True)

    # Downloading remote timestamps json file
    try:
        object = s3.Object(bucket, remote_timestamp_file_path).get()
        file_content = object['Body'].read().decode('utf-8')
        timestamps_remote = json.loads(file_content)
    except botocore.exceptions.ClientError as e:
        if e.response['Error']['Code'] == "NoSuchKey":
            # The object does not exist.
            print('No remote timestamps file found')
            return
        else:
            # Something else has gone wrong.
            print("Error while retrieving remote timestamp file.")
            print(e.response)
            return

    # Loading local timestamps file if present
    local_timestamp_path = join(local_paper_matrix_dir_path, timestamp_file_name)
    if not exists(local_timestamp_path):
        timestamps_local = {}
    else:
        with open(local_timestamp_path, 'r') as f:
            timestamps_local = json.load(f)

    # Download new files if remote timestamp is older than local timestamp
    for key, timestamp in timestamps_remote.items():
        if not key in timestamps_local or dateutil.parser.parse(timestamps_local[key]) < dateutil.parser.parse(
                timestamp):
            print("\tRefreshing Paper Matrix: " + key)
            download_file(join(remote_paper_matrix_dir_path, key + paper_matrix_file_extension),
                          join(local_paper_matrix_dir_path, key + paper_matrix_file_extension))

    # Write new timestamps file
    with open(local_timestamp_path, 'w') as f:
        json.dump(timestamps_remote, f)


if __name__ == '__main__':
    print("Sync Starting")
    print("Syncing sentence transformer model")
    sync_zipped_model('sentence_transformer')
    print("Syncing lda model")
    sync_zipped_model('lda')
    print("Syncing paper matrix")
    sync_paper_matrix()
