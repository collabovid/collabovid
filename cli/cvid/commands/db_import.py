import os

from .abstract.s3_command import S3Command


class ImportCommand(S3Command):
    def __init__(self, config, user_config):
        super().__init__(config, user_config)
        self.s3_bucket_client = None

    def _get_s3_archives(self):
        if not self.s3_bucket_client:
            self.s3_bucket_client = self.setup_s3_bucket_client()
        archives = self.s3_bucket_client.all_objects(prefix=self.config["s3-export-dir"])
        return [os.path.basename(archive_path) for archive_path in reversed(archives) if
                           archive_path.endswith('.tar.gz')]

    def run(self, args):
        if args.list:
            archives = self._get_s3_archives()
            for i, archive in enumerate(archives):
                print(f"{i + 1}. {archive}")
        else:
            if args.filename:
                print(f"Download {args.filename} from S3")
                filename = args.filename
            else:
                archives = self._get_s3_archives()
                if len(archives) == 0:
                    print("No S3 archive to download")
                    return
                filename = archives[0]
                print(f"Download newest archive from S3: {filename}")

            local_dir = self.config['local-export-dir']
            local_path = f"{local_dir}/{filename}"
            s3_path = f"{self.config['s3-export-dir']}/{filename}"
            os.makedirs(local_dir, exist_ok=True)

            if not self.s3_bucket_client:
                self.s3_bucket_client = self.setup_s3_bucket_client()
            self.s3_bucket_client.download_file(s3_path, local_path)

    def help(self):
        return (
            "Export all articles including foreign keys and PDF thumbnails "
            "to S3. PKs, topics, topic scores and topic assignments are ignored."
        )

    def add_arguments(self, parser):
        parser.add_argument(
            "-l", "--list", help="List local data archives", action="store_true"
        )
        parser.add_argument('filename', nargs='?')

    def name(self):
        return "import"
