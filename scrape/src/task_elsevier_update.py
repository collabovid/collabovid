from django.conf import settings

from src.updater.elsevier_update import ElsevierUpdater
from tasks.definitions import register_task, Runnable


@register_task
class ElsevierUpdateTask(Runnable):
    @staticmethod
    def task_name():
        return "update-elsevier"

    def __init__(self, count: int = 100, update_pdf_image: bool = True, *args, **kwargs):
        super(ElsevierUpdateTask, self).__init__(*args, **kwargs)
        self.count = count
        self.update_pdf_image = update_pdf_image

    def run(self):
        if not settings.ALLOW_IMAGE_SCRAPING:
            pdf_image = False
            self.log("Scraping images disabled in settings")
        else:
            pdf_image = self.update_pdf_image

        updater = ElsevierUpdater(log=self.log, pdf_image=pdf_image, pdf_content=False, update_existing=True)
        updater.update_existing_data(count=self.count, progress=self.progress)


@register_task
class ElsevierNewArticlesTask(Runnable):
    @staticmethod
    def task_name():
        return "get-new-elsevier"

    def __init__(self, *args, **kwargs):
        super(ElsevierNewArticlesTask, self).__init__(*args, **kwargs)

    def run(self):
        if not settings.ALLOW_IMAGE_SCRAPING:
            pdf_image = False
            self.log("Scraping images disabled in settings")
        else:
            pdf_image = True

        updater = ElsevierUpdater(log=self.log, pdf_image=pdf_image, pdf_content=False, update_existing=False)
        updater.get_new_data(progress=self.progress)
