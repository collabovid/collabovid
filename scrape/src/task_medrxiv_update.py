from django.conf import settings
from src.updater.medrxiv_update import MedrxivUpdater
from tasks.definitions import register_task, Runnable


@register_task
class MedBiorxivUpdateTask(Runnable):
    @staticmethod
    def task_name():
        return "update-medbiorxiv"

    def __init__(self, count: int = 200, update_pdf_image: bool = True, *args, **kwargs):
        super(MedBiorxivUpdateTask, self).__init__(*args, **kwargs)
        self.count = count
        self.update_pdf_image = update_pdf_image

    def run(self):
        if not settings.ALLOW_IMAGE_SCRAPING:
            pdf_image = False
            self.log("Scraping images disabled in settings")
        else:
            pdf_image = self.update_pdf_image

        updater = MedrxivUpdater(log=self.log)
        updater.update_existing_data(count=self.count, pdf_image=pdf_image)


@register_task
class MedBiorxivNewArticlesTask(Runnable):
    @staticmethod
    def task_name():
        return "get-new-medbiorxiv"

    def __init__(self, *args, **kwargs):
        super(MedBiorxivNewArticlesTask, self).__init__(*args, **kwargs)

    def run(self):
        if not settings.ALLOW_IMAGE_SCRAPING:
            pdf_image = False
            self.log("Scraping images disabled in settings")
        else:
            pdf_image = True

        updater = MedrxivUpdater(log=self.log)
        updater.get_new_data(pdf_content=True, pdf_image=pdf_image)