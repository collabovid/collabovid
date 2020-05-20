from cvid.commands.abstract.abstract_jobs import AbstractJobsCommand


class JobsCommand(AbstractJobsCommand):

    def run(self, args):
        if args.command == 'run':
            job_file = self.get_job_file(job_name=args.name)
            # Check if the old job is still present because when starting a job, the old one must be deleted
            if self.resource_exists('job', args.name):
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
