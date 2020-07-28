from django.conf import settings
from django.db.models import F
from pyaltmetric import AltmetricException, HTTPException as AltmetricHTTPException

from data.models import Paper
from src.altmetric.altmetric_update import AltmetricUpdate
from tasks.definitions import register_task, Runnable


@register_task
class AltmetricUpdateTask(Runnable):
    MAX_ERRORS = 50

    @staticmethod
    def task_name():
        return "get-altmetric-data"

    def __init__(self, update_all: bool = False, max_count: int = 50, *args, **kwargs):
        super(AltmetricUpdateTask, self).__init__(*args, **kwargs)
        self.max_count = max_count
        self.update_all = update_all

    def run(self):
        if not settings.ALTMETRIC_KEY:
            self.log("Altmetric API key not specified. Set environment variable 'ALTMETRIC_KEY'")
            raise

        altmetric_update = AltmetricUpdate(api_key=settings.ALTMETRIC_KEY)

        papers = Paper.objects.all().order_by(F('last_altmetric_update').asc(nulls_first=True))

        if not self.update_all:
            self.log(f"Update Altmetric data of {self.max_count} articles")
            papers = papers[:self.max_count]
        else:
            self.log("Update Altmetric data of all articles")

        n_errors = 0
        for paper in self.progress(papers):
            try:
                altmetric_update.update(paper)
            except (AltmetricException, AltmetricHTTPException) as ex:
                self.log(f"Error at paper {paper.doi}: {ex}")
                n_errors += 1
            if n_errors >= self.MAX_ERRORS:
                break

        if n_errors > 0:
            raise Exception("Failed to update all Altmetric scores")
