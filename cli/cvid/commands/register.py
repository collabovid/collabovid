#

from .command import Command, KubectlCommand
import os
from os.path import join


class RegisterCommand(Command):
    def run(self, args):
        super().run(args)

        self.run_shell_command(
            f"eksctl create iamidentitymapping --cluster {args.cluster} --arn {args.arn} "
            f"--group system:masters --username {args.username}")

    def add_arguments(self, parser):
        super().add_arguments(parser)
        parser.add_argument('--arn', type=str)
        parser.add_argument('--cluster', type=str)
        parser.add_argument('--username', type=str)

    def help(self):
        return "Adds user to the cluster"

    def name(self):
        return "register"
