from .command import Command
from os.path import join
import os
from collabovid_store.s3_utils import S3BucketClient
from collabovid_store.stores import ModelsStore, PaperMatrixStore

paper_matrices = [
    'lda',
    'title_sentence_vectorizer'
]

class UploadModelsCommand(Command):
    def run(self, args):
        models_directory = join(os.getcwd(), args.directory)
        aws_access_key = self.current_env_config()['s3_access_key']
        aws_secret_access_key = self.current_env_config()['s3_secret_access_key']
        endpoint_url = self.current_env_config()['s3_endpoint_url']
        bucket = self.current_env_config()['s3_bucket_name']
        s3_bucket_client = S3BucketClient(aws_access_key=aws_access_key, aws_secret_access_key=aws_secret_access_key,
                                          endpoint_url=endpoint_url, bucket=bucket)
        if args.models is not None:
            self.print_info('Uploading Models')
            models_store = ModelsStore(s3_bucket_client)
            models_store.update_remote(models_directory, args.models)

        if args.paper_matrices is not None:
            self.print_info('Processing Paper Matrices')
            paper_matrix_store = PaperMatrixStore(s3_bucket_client)
            paper_matrix_store.update_remote(join(models_directory, 'paper_matrix'), args.paper_matrices)

    def add_arguments(self, parser):
        parser.add_argument('-d', '--directory', help="Models directory", default='models')
        parser.add_argument('-m', '--models', nargs='*', choices=['lda', 'small_sentence_transformer'])
        parser.add_argument('-p', '--paper-matrices', nargs='*', choices=paper_matrices)

    def help(self):
        return "Upload models to s3"

    def name(self):
        return "upload-models"
