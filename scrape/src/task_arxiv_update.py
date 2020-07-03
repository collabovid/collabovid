from django.conf import settings
from src.updater.arxiv_update import ArxivUpdater
from tasks.definitions import register_task, Runnable


@register_task
class ArxivUpdateTask(Runnable):
    @staticmethod
    def task_name():
        return "update-arxiv"

    def __init__(self, count: int = 20, update_pdf_image: bool = True, *args, **kwargs):
        super(ArxivUpdateTask, self).__init__(*args, **kwargs)
        self.count = count
        self.update_pdf_image = update_pdf_image

    def run(self):
        if not settings.ALLOW_IMAGE_SCRAPING:
            pdf_image = False
            self.log("Scraping images disabled in settings")
        else:
            pdf_image = self.update_pdf_image

        updater = ArxivUpdater(log=self.log)
        updater.update_existing_data(count=self.count, pdf_image=pdf_image, progress=self.progress)


@register_task
class ArxivNewArticlesTask(Runnable):
    @staticmethod
    def task_name():
        return "get-new-arxiv"

    def __init__(self, *args, **kwargs):
        super(ArxivNewArticlesTask, self).__init__(*args, **kwargs)

    def run(self):
        if not settings.ALLOW_IMAGE_SCRAPING:
            pdf_image = False
            self.log("Scraping images disabled in settings")
        else:
            pdf_image = True

        updater = ArxivUpdater(log=self.log)
        updater.get_new_data(pdf_content=True, pdf_image=pdf_image, progress=self.progress)
