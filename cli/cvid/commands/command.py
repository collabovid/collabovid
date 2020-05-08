import subprocess
import argparse
from os.path import join, exists
import os


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

    def current_env(self):
        return self.config['env']

    def build_kubernetes_config(self):
        env = self.current_env()
        kubernetes_dir = join(os.getcwd(), 'k8s')
        if not exists(kubernetes_dir):
            print('Did not find k8s directory in cwd')
            exit(1)
        temp_dir = join(kubernetes_dir, 'tmp')
        kubernetes_env_dir = join(kubernetes_dir, 'overlays', env)
        self.run_shell_command('mkdir -p {} && cp -r {} {}'.format(temp_dir, kubernetes_env_dir, temp_dir))
        for repo, config in self.config['repositories'].items():
            tag = config['version']
            registry = self.current_env_config()['registry']
            if len(registry) > 0:
                registry += '/'
            self.run_shell_command(
                '(cd {} && kustomize edit set image {}={}{}:{})'.format(join(temp_dir, env), repo, registry, repo, tag))

        options_dir = join(kubernetes_dir, 'options')
        for option in self.current_env_config()['optionFiles']:
            option_file_path = join(options_dir, option)
            if not exists(option_file_path):
                print("Unknown optionFiles item specified in config: {}".format(option))
                exit(2)
            self.run_shell_command("cp {} {}".format(option_file_path, join(temp_dir, env, 'option-' + option)))
            self.run_shell_command("(cd {} && kustomize edit add patch {})".format(join(temp_dir, env), ('option-' + option)))
        self.run_shell_command('{} {} {}'.format(join(kubernetes_dir, 'build.sh'), join(temp_dir, env), env))
        self.run_shell_command('rm -rf {}'.format(temp_dir))

    def help(self):
        return ""

    def current_env_config(self):
        return self.config['envs'][self.current_env()]

    def name(self):
        return ""


class CommandWithRepositories(Command):
    def run(self, args):
        if args.all:
            args.repositories = self.config['repositories'].items()
            print("No Repository specified: Running for all..")
        else:
            args.repositories = [(repository, self.config['repositories'][repository]) for repository in
                                 args.repositories]

    def add_arguments(self, parser):
        group = parser.add_mutually_exclusive_group(required=True)
        group.add_argument('--all', action='store_true')
        group.add_argument('-r', '--repositories', nargs='*', choices=self.config['repositories'].keys(),
                           help="Specify multiple values of {} or use all".format(self.config['repositories'].keys()))
