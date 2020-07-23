from django.conf import settings

from src.updater.pubmed_update import PubmedUpdater
from tasks.definitions import register_task, Runnable


@register_task
class PubmedUpdateTask(Runnable):
    @staticmethod
    def task_name():
        return "update-pubmed"

    def __init__(self, count: int = 100, update_pdf_image: bool = True, force_update: bool = False, *args, **kwargs):
        super(PubmedUpdateTask, self).__init__(*args, **kwargs)
        self.count = count
        self.update_pdf_image = update_pdf_image
        self.force_update = force_update

    def run(self):
        if not settings.ALLOW_IMAGE_SCRAPING:
            pdf_image = False
            self.log("Scraping images disabled in settings")
        else:
            pdf_image = self.update_pdf_image

        updater = PubmedUpdater(log=self.log, pdf_image=pdf_image, pdf_content=False,
                                update_existing=True, force_update=self.force_update)
        updater.update_existing_data(count=self.count, progress=self.progress)


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

        updater = PubmedUpdater(log=self.log, pdf_image=pdf_image, pdf_content=False, update_existing=False)
        updater.get_new_data(progress=self.progress)
