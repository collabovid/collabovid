from os.path import join
import os
from cvid.commands.abstract.s3_command import S3SyncCommand
from collabovid_store.stores import ModelsStore


class ModelsCommand(S3SyncCommand):
    def run(self, args):
        super().run(args)
        directory = join(os.getcwd(), args.directory)
        s3_bucket_client = self.setup_s3_bucket_client()
        models_store = ModelsStore(s3_bucket_client)

        if args.command == 'upload':
            self.print_info('Uploading Models')
            models_store.update_remote(directory, args.names)
        elif args.command == 'download':
            self.print_info("Downloading")
            models_store.sync_to_local_directory(directory, keys=[f'{key}.zip' for key in args.names], force=args.force)

    @property
    def default_directory(self):
        return 'models'

    @property
    def name_choices(self):
        return ['lda', 'sentence_transformer', 'litcovid_longformer_base', 'en_core_web_lg']

    def help(self):
        return "Upload/download models"

    def name(self):
        return "models"
