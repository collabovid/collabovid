from .command import Command
from os.path import join


class CronJobsCommand(Command):
    def run(self, args):
        kubectl = self.current_env_config()['kubectl']
        base_path = join('k8s', 'dist')
        job_file = join(base_path, 'cronjobs', self.current_env(), 'cronjob--{}.yml'.format(args.name))
        if args.command == 'run':
            self.build_kubernetes_config()
            self.run_shell_command("{} delete -f {}".format(kubectl, job_file))
            self.run_shell_command("{} apply -f {}".format(kubectl, job_file))
        elif args.command == 'logs':
            self.run_shell_command("{} logs  --selector=cronjob-name={}".format(kubectl, args.name))
        elif args.command == 'status':
            self.run_shell_command("{} get pods --selector=cronjob-name={}".format(kubectl, args.name))

    def add_arguments(self, parser):
        parser.add_argument('command', choices=['run', 'logs', 'status'])
        parser.add_argument('name')

    def help(self):
        return "Manage Kubernetes cronjobs"

    def name(self):
        return "cronjobs"
