import subprocess
import argparse


class Command:
    def __init__(self, config, user_config):
        self.config = config
        self.user_config = user_config

    def run(self, args):
        raise NotImplementedError()

    def add_arguments(self, parser):
        pass

    def run_shell_command(self, cmd):
        self.print_info("Running: {}".format(cmd))
        return subprocess.run(cmd, shell=True)

    def print_info(self, info):
        ansi_cyan = "\033[1;36m"
        ansi_reset = "\u001B[0m"
        print(ansi_cyan + info + ansi_reset)

    def help(self):
        return ""

    def current_env_config(self):
        return self.config['envs'][self.config['env']]

    def name(self):
        return ""


class CommandWithRepositories(Command):
    def run(self, args):
        if args.all:
            args.repositories = self.config['repositories'].items()
            print("No Repository specified: Running for all..")
        else:
            args.repositories = [(repository, self.config['repositories'][repository]) for repository in args.repositories]

    def add_arguments(self, parser):
        group = parser.add_mutually_exclusive_group(required=True)
        group.add_argument('--all', action='store_true')
        group.add_argument('-r', '--repositories', nargs='*', choices=self.config['repositories'].keys(),
                           help="Specify multiple values of {} or use all".format(self.config['repositories'].keys()))
