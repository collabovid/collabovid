import os

from .abstract.s3_command import S3Command


class ExportCommand(S3Command):
    def _get_local_archives(self):
        return sorted(
            [
                x
                for x in os.listdir(self.config["local-export-dir"])
                if x.endswith(".tar.gz")
            ],
            reverse=True,
        )

    def run(self, args):
        if args.list:
            archives = self._get_local_archives()
            for i, archive in enumerate(archives):
                print(f"{i + 1}. {archive}")
        else:
            if args.filename:
                print(f"Upload {args.filename} to S3")
                filename = args.filename
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

            s3_bucket_client = self.setup_s3_bucket_client()
            s3_bucket_client.upload(path, f"{self.config['s3-export-dir']}/{args.filename}")

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
        return "export"
