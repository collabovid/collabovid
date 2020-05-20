from cvid.commands.command import Command
from collabovid_store.s3_utils import S3BucketClient
import os


class S3Command(Command):
    def setup_s3_bucket_client(self):
        aws_access_key = self.current_env_config()['s3_access_key']
        aws_secret_access_key = self.current_env_config()['s3_secret_access_key']
        endpoint_url = self.endpoint_url
        bucket = self.current_env_config()['s3_bucket_name']
        s3_bucket_client = S3BucketClient(aws_access_key=aws_access_key, aws_secret_access_key=aws_secret_access_key,
                                          endpoint_url=endpoint_url, bucket=bucket)
        return s3_bucket_client

    @property
    def endpoint_url(self):
        return self.current_env_config()['s3_endpoint_url']

    def add_arguments(self, parser):
        pass


class S3SyncCommand(S3Command):

    def run(self, args):
        if args.all:
            args.names = self.name_choices
        if args.command == 'upload':
            self.print_info(f"Uploading will happen in env '{self.current_env()}' to url: {self.endpoint_url}")
            confirmation = self.ask_for_confirmation("Do you want to continue?")
            if not confirmation:
                exit(1)
        os.makedirs(args.directory, exist_ok=True)

    def add_arguments(self, parser):
        parser.add_argument('-d', '--directory', help="Local Directory that should be used to upload/download",
                            default=self.default_directory)
        parser.add_argument('-f', '--force', help="Download even when version is latest",
                            action='store_true')
        parser.add_argument('command', choices=['upload', 'download'])
        group = parser.add_mutually_exclusive_group(required=True)
        group.add_argument('--all', action='store_true')
        group.add_argument('-n', '--names', nargs='+', choices=self.name_choices,
                           help="Specify names to upload/download")

    @property
    def default_directory(self):
        return 'models'

    @property
    def name_choices(self):  #
        return []
