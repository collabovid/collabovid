from os.path import join
import os
from cvid.commands.abstract.s3_command import S3SyncCommand
from collabovid_store.stores import PaperMatrixStore


class PaperMatricesCommand(S3SyncCommand):
    def run(self, args):
        super().run(args)
        directory = join(os.getcwd(), args.directory)
        s3_bucket_client = self.setup_s3_bucket_client()

        paper_matrix_store = PaperMatrixStore(s3_bucket_client)
        if args.command == 'upload':
            self.print_info('Uploading Paper Matrices')
            paper_matrix_store.update_remote(directory, args.names)
        elif args.command == 'download':
            self.print_info("Downloading Paper Matrices")
            paper_matrix_store.sync_to_local_directory(directory, keys=[f'{key}.pkl' for key in args.names], force=args.force)

    @property
    def default_directory(self):
        return 'models/paper_matrix'

    @property
    def name_choices(self):
        return ['transformer_paper_oubiobert_512', 'transformer_paper_no_locations', 'transformer_paper_sensitive_512']

    def help(self):
        return "Upload/download paper matrices to s3"

    def name(self):
        return "paper-matrices"
