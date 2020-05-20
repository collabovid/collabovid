from os.path import join
from cvid.commands.abstract.kubectl import KubectlCommand


class AbstractJobsCommand(KubectlCommand):
    def run(self, args):
        super().run(args)
        if args.command == 'logs':
            self.run_shell_command(
                f"{self.kubectl} logs  --tail=-1 --selector={self.get_job_identifier()}-name={args.name}")
        elif args.command == 'apply':
            self.run_shell_command(f"{self.kubectl} apply -f {self.get_job_file(args.name)}")
        elif args.command == 'status':
            self.run_shell_command(f"{self.kubectl} get pods --selector={self.get_job_identifier()}-name={args.name}")
        elif args.command == 'delete':
            if args.all:
                self.run_shell_command(f'{self.kubectl} delete {self.get_job_identifier()}s --all')
            else:
                self.run_shell_command(f"{self.kubectl} delete {self.get_job_identifier()} {args.name}")

    def get_job_file(self, job_name):
        return join(self.k8s_dist_path, f"{self.get_job_identifier()}s", self.current_env(),
                    f'{self.get_job_identifier()}--{job_name}.yml')

    def add_arguments(self, parser):
        super().add_arguments(parser)
        parser.add_argument('command', choices=self.command_choices())
        group = parser.add_mutually_exclusive_group(required=True)
        group.add_argument('--all', action='store_true')
        group.add_argument('-n', '--name')

    def command_choices(self):
        return ['logs', 'status', 'delete', 'apply']

    def get_job_identifier(self):
        return ''
