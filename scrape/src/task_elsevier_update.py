from django.conf import settings

from src.updater.elsevier_update import ElsevierUpdater
from tasks.definitions import register_task, Runnable


# @register_task
# class PubmedUpdateTask(Runnable):
#     @staticmethod
#     def task_name():
#         return "update-pubmed"
#
#     def __init__(self, count: int = 10, update_pdf_image: bool = True, *args, **kwargs):
#         super(PubmedUpdateTask, self).__init__(*args, **kwargs)
#         self.count = count
#         self.update_pdf_image = update_pdf_image
#
#     def run(self):
#         if not settings.ALLOW_IMAGE_SCRAPING:
#             pdf_image = False
#             self.log("Scraping images disabled in settings")
#         else:
#             pdf_image = self.update_pdf_image
#
#         updater = PubmedUpdater(log=self.log)
#         updater.update_existing_data(count=self.count, pdf_image=pdf_image)


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

        updater = ElsevierUpdater(log=self.log)
        updater.get_new_data(pdf_content=True, pdf_image=pdf_image)
