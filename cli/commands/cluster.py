from .command import Command
import os
from os.path import join

commands = {
    'apply': 'apply',
    'restart': 'rollout restart',
    'replace': 'replace',
    'delete': 'delete'
}


class ClusterCommand(Command):
    def run(self, args):
        if args.name and not args.resource:
            print('No resource type supplied. Use -r <resource>. Exiting.')
            return
        kubectl = self.current_env_config()['kubectl']
        self.run_shell_command('k8s/build.sh')
        path = ''
        base_path = join('k8s', 'dist')
        env_path = join(base_path, self.config["env"])
        if not args.resource and args.all:
            path = '-f ' + env_path
        elif args.resource:
            if args.all:
                for file in os.listdir(env_path):
                    if file.startswith(args.resource):
                        path += " -f {}".format(join(env_path, file))
            elif args.name:
                path = '-f ' + join(env_path, '{}--{}.yml').format(args.resource, args.name)
        self.run_shell_command("{} {} {}".format(kubectl, commands[args.command], path))

    def add_arguments(self, parser):
        parser.add_argument('command', choices=commands.keys())
        parser.add_argument('-r', '--resource', choices=['service', 'deployment', 'secret', 'cronjob', 'daemonset'])
        group = parser.add_mutually_exclusive_group(required=True)
        group.add_argument('--all', action='store_true')
        group.add_argument('-n', '--name')

    def help(self):
        return "Run Commands on the cluster"

    def name(self):
        return "cluster"
