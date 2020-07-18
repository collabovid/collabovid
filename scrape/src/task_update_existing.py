from tasks.task_runner import TaskRunner
from src.geo.task_geo_parser import GeoParserTask
from src.task_medrxiv_update import MedBiorxivUpdateTask
from src.task_arxiv_update import ArxivUpdateTask
from src.task_pubmed_update import PubmedUpdateTask
from src.task_elsevier_update import ElsevierUpdateTask

from tasks.definitions import Runnable, register_task
from tasks.launcher.task_launcher import get_task_launcher
from django.conf import settings


@register_task
class UpdateExistingTask(Runnable):
    @staticmethod
    def task_name():
        return "update-existing-articles"

    def __init__(self,
                 *args, **kwargs):
        super(UpdateExistingTask, self).__init__(*args, **kwargs)

    def run(self):
        self.log("Updating medRxiv/bioRxiv articles...")
        TaskRunner.run_task(MedBiorxivUpdateTask,
                            started_by=self._task.started_by)
        self.log("Finished updating medRxiv/bioRxiv articles...")

        self.progress(15)

        self.log("Updating arXiv articles...")
        TaskRunner.run_task(ArxivUpdateTask,
                            started_by=self._task.started_by)

        self.progress(30)

        self.log("Finished updating arXiv articles...")

        self.log("Updating Elsevier articles...")
        TaskRunner.run_task(ElsevierUpdateTask,
                            started_by=self._task.started_by)
        self.log("Finished updating Elsevier articles...")

        self.progress(45)

        self.log("Updating Pubmed articles...")
        TaskRunner.run_task(PubmedUpdateTask,
                            started_by=self._task.started_by)
        self.log("Finished updating Pubmed articles...")

        self.progress(60)

        if settings.UPDATE_VECTORIZER:
            self.log("Updating Topic assigment...")
            task_launcher = get_task_launcher('search')

            task_config = {
                'service': 'search',
                'parameters': [],
                'started_by': self._task.started_by
            }
            task_launcher.launch_task(name="setup-vectorizer", config=task_config, block=True)
            self.progress(70)
            self.log("Finished setup-vectorizer")

            task_launcher.launch_task(name="update-category-assignment", config=task_config, block=True)
            self.progress(80)
            self.log("Finished updating category assigment")

            task_launcher.launch_task(name="nearest-neighbor-topic-assignment", config=task_config, block=True)
            self.progress(90)
            self.log("Finished nearest-neighbor-topic-assignment")

            task_launcher.launch_task(name="reduce-embedding-dimensionality", config=task_config, block=True)
            self.log("Finished reduce-embedding-dimensionality")
            self.progress(95)
        else:
            self.log("Paper matrix update and topic assignment skipped.")

        self.log("Extract locations from papers...")
        TaskRunner.run_task(GeoParserTask,
                            started_by=self._task.started_by)
        self.log("Finished extracting locations from papers")
