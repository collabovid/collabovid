from django.conf import settings

from scrape.updater.pubmed_update import PubmedUpdater
from tasks.definitions import register_task, Runnable


@register_task
class PubmedUpdateTask(Runnable):
    @staticmethod
    def task_name():
        return "update-pubmed"

    def __init__(self, *args, **kwargs):
        super(PubmedUpdateTask, self).__init__(*args, **kwargs)

    def run(self):
        if not settings.ALLOW_IMAGE_SCRAPING:
            pdf_image = False
            self.log("Scraping images disabled in settings")
        else:
            pdf_image = True
        updater = PubmedUpdater(log=self.log)
        updater.update_existing_data(count=200, pdf_image=pdf_image)


@register_task
class PubmedNewArticlesTask(Runnable):
    @staticmethod
    def task_name():
        return "get-new-pubmed"

    def __init__(self, *args, **kwargs):
        super(PubmedNewArticlesTask, self).__init__(*args, **kwargs)

    def run(self):
        if not settings.ALLOW_IMAGE_SCRAPING:
            pdf_image = False
            self.log("Scraping images disabled in settings")
        else:
            pdf_image = True

        updater = PubmedUpdater(log=self.log)
        updater.get_new_data(pdf_content=True, pdf_image=pdf_image)
