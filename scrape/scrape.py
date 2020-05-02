import os
from tasks.task_runner import TaskRunner
from scrape.task_medrxiv_update import MedrxivUpdateTask
from scrape.task_cord19_update import Cord19UpdateTask
from scrape.task_arxiv_update import ArxivUpdateTask
from scrape.pdf_scraper import PdfScraper
from analyze.update_topic_assignment import UpdateTopicAssignment
from analyze.setup_vectorizer import SetupVectorizer
from tasks import Runnable
from data.models import Paper

from django.conf import settings

class Scrape(Runnable):
    @staticmethod
    def task_name():
        return "scrape"

    def __init__(self,
                 scrape_citations: bool = True,
                 scrape_images: bool = True,
                 scrape_contents: bool = True,
                 update_unknown_category=False,
                 started_by="",
                 *args, **kwargs):
        super(Scrape, self).__init__(*args, **kwargs)

        self._scrape_citations = scrape_citations
        self._scrape_images = scrape_images
        self._scrape_contents = scrape_contents
        self._update_unknown_category = update_unknown_category
        self._started_by = started_by

    def run(self):
        self.log("Scraping articles...")
        TaskRunner.run_task(MedrxivUpdateTask, update_unknown_category=self._update_unknown_category,
                            started_by=self._started_by)
        self.log("Finished scraping articles...")
        self.log("Scraping pdf images and content...")

        scrape_images = self._scrape_images
        if not settings.ALLOW_IMAGE_SCRAPING:
            scrape_images = False
            self.log("Scraping images disabled in settings...")

        TaskRunner.run_task(PdfScraper, papers=Paper.objects.all(), scrape_content=self._scrape_contents,
                            scrape_images=scrape_images, started_by=self._started_by)
        self.log("Finished scraping pdf images and content...")

        if 'USE_PAPER_ANALYZER' in os.environ and os.environ['USE_PAPER_ANALYZER'] == '1':
            self.log("Updating Topic assigment...")
            TaskRunner.run_task(SetupVectorizer, started_by=self._started_by)
            TaskRunner.run_task(UpdateTopicAssignment, started_by=self._started_by)
            self.log("Finished updating topic assigment")
        else:
            self.log("Paper matrix update and topic assignment skipped.")

        self.log("Citation update skipped..")

