import subprocess
import argparse
from os.path import join, exists
import os
from subprocess import PIPE


class Command:
    def __init__(self, config, user_config):
        self.config = config
        self.user_config = user_config

    def run(self, args):
        raise NotImplementedError()

    def add_arguments(self, parser):
        pass

    @property
    def kubectl(self):
        return self.current_env_config()['kubectl']

    def run_shell_command(self, cmd, cwd=None, collect_output=False, print_command=True, quiet=False):
        if print_command and not quiet:
            self.print_info("Running: {}".format(cmd))

        collect_output = collect_output or quiet
        if collect_output:
            return subprocess.run(cmd, shell=True, cwd=cwd, stdout=PIPE)
        else:
            subprocess.run(cmd, shell=True, cwd=cwd)

    def print_info(self, info):
        ansi_cyan = "\033[1;36m"
        ansi_reset = "\u001B[0m"
        print(ansi_cyan + info + ansi_reset)

    def current_env(self):
        return self.config['env']

    def help(self):
        return ""

    def current_env_config(self):
        return self.config['envs'][self.current_env()]

    @property
    def services(self):
        return self.config['services']

    def name(self):
        return ""

    def call_command(self, cmd, *args, **kwargs):
        return self.run_shell_command(f'cvid {cmd}', *args, **kwargs)

    def generate_tag(self):
        result = subprocess.run("echo $(date +%Y%m%d).$(git log -1 --pretty=%h)", shell=True, stdout=PIPE)
        tag = result.stdout.decode('utf-8').strip()
        return tag

    def build_kubernetes_config(self, image_tag=None, customize_callback=None, quiet=True):
        env = self.current_env()
        kubernetes_dir = join(os.getcwd(), 'k8s')
        if not exists(kubernetes_dir):
            print('Did not find k8s directory in cwd')
            exit(1)
        temp_dir = join(kubernetes_dir, 'tmp')
        kubernetes_env_dir = join(kubernetes_dir, 'overlays', env)
        self.run_shell_command('mkdir -p {} && cp -r {} {}'.format(temp_dir, kubernetes_env_dir, temp_dir), quiet=quiet)
        for repo, config in self.config['services'].items():
            if image_tag is None:
                image_tag = self.generate_tag()
            registry = self.current_env_config()['registry']
            if len(registry) > 0:
                registry += '/'
            self.run_shell_command(
                '(cd {} && kustomize edit set image {}={}{}:{})'.format(join(temp_dir, env), repo, registry, repo,
                                                                        image_tag), quiet=quiet)

        options_dir = join(kubernetes_dir, 'options')
        for option in self.current_env_config()['optionFiles']:
            option_file_path = join(options_dir, option)
            if not exists(option_file_path):
                print("Unknown optionFiles item specified in config: {}".format(option))
                exit(2)
            self.run_shell_command("cp {} {}".format(option_file_path, join(temp_dir, env, 'option-' + option)),
                                   quiet=quiet)
            self.run_shell_command(
                "(cd {} && kustomize edit add patch {})".format(join(temp_dir, env), ('option-' + option)), quiet=quiet)

        # allow caller to add further customization
        if customize_callback is not None:
            customize_callback(join(temp_dir, env))

        self.run_shell_command('{} {} {}'.format(join(kubernetes_dir, 'build.sh'), join(temp_dir, env), env), quiet=quiet)
        self.run_shell_command('rm -rf {}'.format(temp_dir), quiet=quiet)


class CommandWithServices(Command):
    def run(self, args):
        if args.all:
            args.services = self.config['services'].items()
            print("No Service specified: Running for all..")
        else:
            args.services = [(service, self.config['services'][service]) for service in args.services]

    def add_arguments(self, parser):
        group = parser.add_mutually_exclusive_group(required=True)
        group.add_argument('--all', action='store_true')
        group.add_argument('-s', '--services', nargs='*', choices=self.config['services'].keys(),
                           help="Specify multiple values of {} or use all".format(self.config['services'].keys()))


class KubectlCommand(Command):
    def run(self, args):
        if not args.no_config_build:
            self.build_kubernetes_config(image_tag=args.tag)

    def add_arguments(self, parser):
        parser.add_argument('-t', '--tag', default=None,
                            help="Specifies the image tag that should be used when building the cluster config")
        parser.add_argument('--no-config-build', action='store_true')

    @property
    def k8s_dist_path(self):
        return join('k8s', 'dist')

    @property
    def k8s_dist_env_path(self):
        return join(self.k8s_dist_path, self.current_env())


class AbstractJobsCommand(KubectlCommand):
    def run(self, args):
        super().run(args)
        job_identifier = self.get_job_identifier()
        job_file = join(self.k8s_dist_path, f"{job_identifier}s", self.current_env(),
                        f'{job_identifier}--{args.name}.yml')
        if args.command == 'run':
            result = self.run_shell_command(
                f'kubectl get jobs --selector={job_identifier}-name={args.name} -o jsonpath={{.items}}',
                collect_output=True, print_command=False)
            if result.stdout.decode('utf8') != '[]':
                self.run_shell_command(f"{self.kubectl} delete -f {job_file}")
            self.run_shell_command(f"{self.kubectl} apply -f {job_file}")
        elif args.command == 'logs':
            self.run_shell_command(f"{self.kubectl} logs  --tail=-1 --selector={job_identifier}-name={args.name}")
        elif args.command == 'status':
            self.run_shell_command(f"{self.kubectl} get pods --selector={job_identifier}-name={args.name}")
        elif args.command == 'delete':
            if args.all:
                self.run_shell_command(f'kubectl delete {job_identifier}s --all')
            else:
                self.run_shell_command(f"{self.kubectl} delete job {args.name}")

    def add_arguments(self, parser):
        super().add_arguments(parser)
        parser.add_argument('command', choices=['run', 'logs', 'status', 'delete'])
        group = parser.add_mutually_exclusive_group(required=True)
        group.add_argument('--all', action='store_true')
        group.add_argument('-n', '--name')

    def get_job_identifier(self):
        return ''
