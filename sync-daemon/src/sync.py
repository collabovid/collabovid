import os
from os.path import join
from collabovid_store.stores import PaperMatrixStore, ModelsStore,ResourcesStore
from collabovid_store.s3_utils import S3BucketClient
import datetime
from time import sleep

aws_access_key = os.getenv('AWS_ACCESS_KEY_ID')
aws_secret_access_key = os.getenv('AWS_SECRET_ACCESS_KEY')
protocol = os.getenv('AWS_S3_PROTOCOL')
aws_s3_host = os.getenv('AWS_S3_HOST')
bucket = os.getenv('AWS_STORAGE_BUCKET_NAME')
aws_base_dir = os.getenv('AWS_BASE_DIR', '')
sync_interval = int(os.getenv('SYNC_INTERVAL', '30'))

s3_bucket_client = S3BucketClient(aws_access_key=aws_access_key, aws_secret_access_key=aws_secret_access_key,
                                  endpoint_url=f"{protocol}://{aws_s3_host}", bucket=bucket)

models_store = ModelsStore(s3_bucket_client, remote_root_path=join(aws_base_dir, 'models'))
paper_matrix_store = PaperMatrixStore(s3_bucket_client, remote_root_path=join(aws_base_dir, 'models', 'paper_matrix'))
resources_store = ResourcesStore(s3_bucket_client, remote_root_path=join(aws_base_dir, 'resources'))

if __name__ == '__main__':
    while True:
        print(f"[{datetime.datetime.now().replace(microsecond=0)}] Sync Starting", flush=True)

        print("\tSyncing models")
        models_store.sync()

        print("\tSyncing paper matrix")
        paper_matrix_store.sync()

        sleep(sync_interval)
