import requests

from tasks.definitions import register_task, Runnable
from scrape.pdf_content_scraper import PdfContentScraper
from scrape.pdf_image_scraper import PdfImageScraper
from data.models import Paper

@register_task
class PdfScraper(Runnable):

    @staticmethod
    def task_name():
        return "scrape-pdf"

    def __init__(self, papers=None, scrape_content=True, scrape_images=True, *args, **kwargs):
        super(PdfScraper, self).__init__(*args, **kwargs)

        if papers:
            self.papers = papers
        else:
            self.papers = Paper.objects.all()

        self._scrape_content = scrape_content
        self._scrape_images = scrape_images

    def run(self):
        if self._scrape_images or self._scrape_content:
            skipped_papers = 0

            for i, paper in enumerate(self.papers):

                response = None

                if self._scrape_images and not paper.preview_image:
                    response = requests.get(paper.pdf_url)
                    PdfImageScraper.load_image_from_pdf_response(self, paper, response)
                    self.log(f"Image {i} finished")

                if self._scrape_content and (not paper.data or not paper.data.content):
                    if response is None:
                        response = requests.get(paper.pdf_url)
                    PdfContentScraper.parse_response(self, paper, response)
                    self.log(f"Content {i} finished")

                if response is None:
                    skipped_papers += 1

            self.log("Skipped", skipped_papers, "papers")
        else:
            self.log("Neither scrape_images nor scrape_content was set to true. Thus, no papers were scraped.")
