import os
from tasks.task_runner import TaskRunner
from src.task_medrxiv_update import MedBiorxivNewArticlesTask
from src.task_arxiv_update import ArxivNewArticlesTask

# from analyze.update_topic_assignment import UpdateTopicAssignment
# from analyze.setup_vectorizer import SetupVectorizer

from tasks.definitions import Runnable, register_task
from tasks.launcher.task_launcher import get_task_launcher
from django.conf import settings


@register_task
class ScrapeTask(Runnable):
    @staticmethod
    def task_name():
        return "scrape"

    def __init__(self,
                 *args, **kwargs):
        super(ScrapeTask, self).__init__(*args, **kwargs)

    def run(self):
        self.log("Get new medRxiv/bioRxiv articles...")
        TaskRunner.run_task(MedBiorxivNewArticlesTask,
                            started_by=self._task.started_by)
        self.log("Finished getting new medRxiv/bioRxiv articles...")

        self.log("Get new arXiv articles...")
        TaskRunner.run_task(ArxivNewArticlesTask,
                            started_by=self._task.started_by)
        self.log("Finished getting new medRxiv/bioRxiv articles...")

        if settings.UPDATE_VECTORIZER:
            self.log("Updating Topic assigment...")
            task_launcher = get_task_launcher()

            task_config = {
                'service': 'search',
                'parameters': [],
                'started_by': self._task.started_by
            }

            task_launcher.launch_task(name="setup-vectorizer", config=task_config, block=True)
            task_launcher.launch_task(name="update-topic-assignment", config=task_config, block=True)

            self.log("Finished updating topic assigment")
        else:
            self.log("Paper matrix update and topic assignment skipped.")
