import os
import re

from .abstract.s3_command import S3Command


class DataCommand(S3Command):
    def __init__(self, config, user_config):
        super().__init__(config, user_config)
        self.s3_bucket_client = None

    def _get_s3_archives(self):
        if not self.s3_bucket_client:
            self.s3_bucket_client = self.setup_s3_bucket_client()
        archives = self.s3_bucket_client.all_objects(prefix=self.config["s3-export-dir"])
        return [os.path.basename(archive_path) for archive_path in reversed(archives)
                if archive_path.endswith('.tar.gz')]

    def _get_filename(self, source, idx):
        archives = self._get_s3_archives() if source == 's3' else self._get_local_archives()
        if len(archives) <= idx:
            print("No S3 archive to download")
            return
        return archives[idx]

    def _get_local_archives(self):
        return sorted(
            [
                x
                for x in os.listdir(self.config["local-export-dir"])
                if x.endswith(".tar.gz")
            ],
            reverse=True,
        )

    def _print_remote_archives(self):
        remote_archives = self._get_s3_archives()
        print("Remote Archives:")
        for i, archive in enumerate(remote_archives):
            print(f"{i}. {archive}")

    def _print_local_archives(self):
        local_archives = self._get_local_archives()
        print("Local Archives:")
        for i, archive in enumerate(local_archives):
            print(f"{i}. {archive}")

    def run(self, args):
        if args.command == 'download':
            if args.list:
                self._print_remote_archives()
            else:
                if args.filename:
                    match = re.match(r'(\d+)\.?', args.filename)
                    if match:
                        filename = self._get_filename(source='s3', idx=int(match.group(1)))
                    else:
                        filename = args.filename
                    print(f"Download {filename} from S3")
                else:
                    filename = self._get_filename(source='s3', idx=0)
                    print(f"Download newest archive from S3: {filename}")

                local_dir = self.config['local-export-dir']
                local_path = f"{local_dir}/{filename}"
                s3_path = f"{self.config['s3-export-dir']}/{filename}"
                os.makedirs(local_dir, exist_ok=True)

                if not self.s3_bucket_client:
                    self.s3_bucket_client = self.setup_s3_bucket_client()
                self.s3_bucket_client.download_file(s3_path, local_path)

        elif args.command == 'upload':
            if args.list:
                self._print_local_archives()
            else:
                if args.filename:
                    match = re.match(r'(\d+)\.?', args.filename)
                    if match:
                        filename = self._get_filename(source='local', idx=int(match.group(1)))
                    else:
                        filename = args.filename
                    print(f"Upload {filename} to S3")
                else:
                    archives = self._get_local_archives()
                    if len(archives) == 0:
                        print("No local archives to upload")
                        return
                    filename = archives[0]
                    print(f"Upload newest archive to S3: {filename}")

                path = f"{self.config['local-export-dir']}/{filename}"
                if not os.path.exists(path):
                    print(f"Archive {path} does not exist")
                    return

                if not self.s3_bucket_client:
                    self.s3_bucket_client = self.setup_s3_bucket_client()
                self.s3_bucket_client.upload(path, f"{self.config['s3-export-dir']}/{filename}")
        elif args.command == 'delete-remote':
            if not args.filename:
                self._print_remote_archives()
            else:
                match = re.match(r'(\d+)\.?', args.filename)
                if match:
                    filename = self._get_filename(source='s3', idx=int(match.group(1)))
                else:
                    filename = args.filename
                print(f"Delete {filename} from S3")
                if not self.s3_bucket_client:
                    self.s3_bucket_client = self.setup_s3_bucket_client()
                s3_path = f"{self.config['s3-export-dir']}/{filename}"
                self.s3_bucket_client.delete_file(s3_path)

    def help(self):
        return (
            "Upload archive to S3 or download from S3 to local storage."
            " Delete remote exports (delete-remote)"
        )

    def add_arguments(self, parser):
        parser.add_argument('command', choices=['upload', 'download', 'delete-remote'])
        parser.add_argument(
            "-l", "--list", help="List local/remote data archives", action="store_true"
        )
        parser.add_argument('filename', nargs='?', help="File to upload/download/delete "
                                                        "(file name or its number in the list)")

    def name(self):
        return "data"