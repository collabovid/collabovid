import os
from tasks.task_runner import TaskRunner
from scrape.src.task_medrxiv_update import MedBiorxivNewArticlesTask
from scrape.src.task_arxiv_update import ArxivNewArticlesTask

#from analyze.update_topic_assignment import UpdateTopicAssignment
#from analyze.setup_vectorizer import SetupVectorizer

from tasks.definitions import Runnable, register_task

# TODO: Call setup vectorizer and update topic assignment
@register_task
class Scrape(Runnable):
    @staticmethod
    def task_name():
        return "scrape"

    def __init__(self,
                 started_by="",
                 *args, **kwargs):
        super(Scrape, self).__init__(*args, **kwargs)
        self._started_by = started_by

    def run(self):
        self.log("Get new medRxiv/bioRxiv articles...")
        TaskRunner.run_task(MedBiorxivNewArticlesTask,
                            started_by=self._started_by)
        self.log("Finished getting new medRxiv/bioRxiv articles...")

        self.log("Get new arXiv articles...")
        TaskRunner.run_task(ArxivNewArticlesTask,
                            started_by=self._started_by)
        self.log("Finished getting new medRxiv/bioRxiv articles...")

        if 'USE_PAPER_ANALYZER' in os.environ and os.environ['USE_PAPER_ANALYZER'] == '1':
            self.log("Updating Topic assigment...")
            #TaskRunner.run_task(SetupVectorizer, started_by=self._started_by)
            #TaskRunner.run_task(UpdateTopicAssignment, started_by=self._started_by)
            self.log("Finished updating topic assigment")
        else:
            self.log("Paper matrix update and topic assignment skipped.")
