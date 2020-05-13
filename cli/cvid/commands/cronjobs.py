from .command import AbstractJobsCommand


class CronJobsCommand(AbstractJobsCommand):

    def get_job_identifier(self):
        return 'cronjob'

    def help(self):
        return "Manage Kubernetes cronjobs"

    def name(self):
        return "cronjobs"
