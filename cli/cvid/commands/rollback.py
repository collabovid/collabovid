from .command import Command
from os.path import exists
import json


class RollbackCommand(Command):
    def run(self, args):
        if not exists(args.file):
            print('Specified Release file does not exist')

        with open(args.file, 'r') as f:
            release_data = json.load(f)

        old_version = release_data['old_version']
        new_version = release_data['new_version']

        # Building the config with the old tag
        self.build_kubernetes_config(image_tag=old_version)

    def add_arguments(self, parser):
        parser.add_argument('-f', '--file', help="Release file where rollback should happen upon")

    def help(self):
        return "Rollbacks the application running on the cluster to a previous version"

    def name(self):
        return "rollback"
