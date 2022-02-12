import os

from src.altmetric.task_get_altmetric_data import AltmetricUpdateTask
from tasks.task_runner import TaskRunner
from src.geo.task_geo_parser import GeoParserTask
from src.task_medrxiv_update import MedBiorxivNewArticlesTask
from src.task_arxiv_update import ArxivNewArticlesTask
from src.task_pubmed_update import PubmedNewArticlesTask
from src.task_elsevier_update import ElsevierNewArticlesTask
from src.task_statistics_update import StatisticsUpdateTask

from tasks.definitions import Runnable, register_task
from tasks.launcher.task_launcher import get_task_launcher
from django.conf import settings


@register_task
class ScrapeTask(Runnable):
    """
    Gets new publications from all data sources and post-processes them.
    This includes categories, visualization, altmetric data and location extraction.
    """

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

        self.progress(10)

        self.log("Get new arXiv articles...")
        TaskRunner.run_task(ArxivNewArticlesTask,
                            started_by=self._task.started_by)

        self.progress(20)

        self.log("Finished getting new arXiv articles...")

        self.log("Get new Elsevier articles...")
        TaskRunner.run_task(ElsevierNewArticlesTask,
                            started_by=self._task.started_by)

        self.progress(40)

        self.log("Get new Pubmed articles...")
        # TaskRunner.run_task(PubmedNewArticlesTask,
        #                    started_by=self._task.started_by)
        self.log("Finished getting new Pubmed articles...")

        # Updating statistics
        TaskRunner.run_task(StatisticsUpdateTask, started_by=self._task.started_by)
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

        self.log("Update Altmetric data of new papers")
        TaskRunner.run_task(AltmetricUpdateTask, started_by=self._task.started_by, update_all=True, only_new=True)
        self.log("Finished updating Altmetric data of new papers")

        self.log("Extract locations from papers...")
        TaskRunner.run_task(GeoParserTask,
                            started_by=self._task.started_by)
        self.log("Finished extracting locations from papers")
