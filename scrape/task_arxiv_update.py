from scrape.scraper.arxiv_scraper import scrape_articles
from tasks import register_task, Runnable


@register_task
class Cord19Downloader(Runnable):
    @staticmethod
    def task_name():
        return "update-arxiv-articles"

    def __init__(self, *args, **kwargs):
        super(Cord19Downloader, self).__init__(*args, **kwargs)

    def run(self):
        scrape_articles()
