import os

from scrape.citation_refresher import CitationRefresher
from tasks.task_runner import TaskRunner
from scrape.article_scraper import ArticleScraper
from scrape.pdf_scraper import PdfScraper
from tasks import Runnable
from data.models import Paper

if 'USE_PAPER_ANALYZER' in os.environ and os.environ['USE_PAPER_ANALYZER'] == '1':
    import analyze


class Scrape(Runnable):

    @staticmethod
    def task_name():
        return "scrape"

    def __init__(self,
                 scrape_citations: bool = True,
                 scrape_images: bool = True,
                 scrape_contents: bool = True,
                 update_unknown_category=False,
                 *args, **kwargs):
        super(Scrape, self).__init__(*args, **kwargs)

        self._scrape_citations = scrape_citations
        self._scrape_images = scrape_images
        self._scrape_contents = scrape_contents
        self._update_unknown_category = update_unknown_category

    def run(self):
        self.log("Scraping articles...")
        TaskRunner.run_task(ArticleScraper, update_unknown_category=self._update_unknown_category)
        self.log("Finished scraping articles...")
        self.log("Scraping pdf images and content...")
        TaskRunner.run_task(PdfScraper, papers=Paper.objects.all(), scrape_content=self._scrape_contents,
                            scrape_images=self._scrape_images)
        self.log("Finished scraping pdf images and content...")

        if 'USE_PAPER_ANALYZER' in os.environ and os.environ['USE_PAPER_ANALYZER'] == '1':
            self.log("Updating paper matrices and topic assignment")
            analyze.get_topic_assignment_analyzer().preprocess()
            analyze.get_topic_assignment_analyzer().assign_to_topics()
            self.log("Finished updating paper matrices and topic assignment")
        else:
            self.log("Paper matrix update and topic assignment skipped.")

        self.log("Updating citations...")
        TaskRunner.run_task(CitationRefresher, only_new=True, count=100)
        self.log("Finished updating citations...")
