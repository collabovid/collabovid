from .command import Command, KubectlCommand
import os
from os.path import join

commands = {
    'apply': 'apply',
    'restart': 'rollout restart',
    'replace': 'replace',
    'delete': 'delete'
}


class ClusterCommand(KubectlCommand):
    def run(self, args):
        super().run(args)
        if args.name and not args.resource:
            print('No resource type supplied. Use -r <resource>. Exiting.')
            return
        path = ''
        if not args.resource and args.all:
            if args.command == 'restart':
                for file in os.listdir(self.k8s_dist_env_path):
                    if file.startswith('deployment') or file.startswith('daemonset'):
                        path += f" -f {join(self.k8s_dist_env_path, file)}"
            else:
                path = '-f ' + self.k8s_dist_env_path
            if args.command == 'delete':
                self.call_command('jobs delete --all --no-config-build')
                self.call_command('cronjobs delete --all --no-config-build')
        elif args.resource:
            if args.all:
                for file in os.listdir(self.k8s_dist_env_path):
                    if file.startswith(args.resource):
                        path += f" -f {join(self.k8s_dist_env_path, file)}"
            elif args.name:
                path = '-f ' + join(self.k8s_dist_env_path, f"{args.resource}--{args.name}.yml")
        self.run_shell_command(f"{self.kubectl} {commands[args.command]} {path}")

    def add_arguments(self, parser):
        super().add_arguments(parser)
        parser.add_argument('command', choices=commands.keys())
        parser.add_argument('-r', '--resource', choices=['service', 'deployment', 'secret', 'cronjob', 'daemonset'])
        group = parser.add_mutually_exclusive_group(required=True)
        group.add_argument('--all', action='store_true')
        group.add_argument('-n', '--name')

    def help(self):
        return "Run Commands on the cluster"

    def name(self):
        return "cluster"
