from .command import AbstractJobsCommand


class JobsCommand(AbstractJobsCommand):

    def run(self, args):
        if args.command == 'run':
            job_file = self.get_job_file(job_name=args.name)
            result = self.run_shell_command(
                f'{self.kubectl} get jobs --selector={self.get_job_identifier()}-name={args.name} -o jsonpath={{.items}}',
                collect_output=True, print_command=False)
            if result.stdout.decode('utf8') != '[]':
                self.run_shell_command(f"{self.kubectl} delete -f {job_file}")
            self.run_shell_command(f"{self.kubectl} apply -f {job_file}")
        else:
            super().run(args)

    def get_job_identifier(self):
        return 'job'

    def command_choices(self):
        return super().command_choices() + ['run']

    def help(self):
        return "Manage Kubernetes jobs"

    def name(self):
        return "jobs"
