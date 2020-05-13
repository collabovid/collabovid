from .command import AbstractJobsCommand


class JobsCommand(AbstractJobsCommand):

    def get_job_identifier(self):
        return 'job'

    def help(self):
        return "Manage Kubernetes jobs"

    def name(self):
        return "jobs"
