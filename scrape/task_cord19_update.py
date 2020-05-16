from django.conf import settings
from scrape.updater.cord19_update import Cord19Updater
from tasks.definitions import register_task, Runnable


@register_task
class Cord19FulltextDownloadTask(Runnable):
    @staticmethod
    def task_name():
        return "download-cord19-fulltext-data"


@register_task
class Cord19UpdateTask(Runnable):
    @staticmethod
    def task_name():
        return "update-cord19"

    def __init__(self, *args, **kwargs):
        super(Cord19UpdateTask, self).__init__(*args, **kwargs)

    def run(self):
        if not settings.ALLOW_IMAGE_SCRAPING:
            pdf_image = False
            self.log("Scraping images disabled in settings")
        else:
            pdf_image = True

        updater = Cord19Updater(log=self.log)
        updater.get_new_data(pdf_content=True, pdf_image=pdf_image)
