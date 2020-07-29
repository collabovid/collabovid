from django.conf import settings
from django.db.models import F, Q
from django.utils import timezone
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

    def __init__(self, update_all: bool = False, max_count: int = 50, only_new: bool = False, once_per_day: bool = True,
                 *args, **kwargs):
        super(AltmetricUpdateTask, self).__init__(*args, **kwargs)
        self.max_count = max_count
        self.update_all = update_all
        self.only_new = only_new
        self.once_per_day = once_per_day

    def run(self):
        if not settings.ALTMETRIC_KEY:
            self.log("Altmetric API key not specified. Set environment variable 'ALTMETRIC_KEY'")
            raise

        altmetric_update = AltmetricUpdate(api_key=settings.ALTMETRIC_KEY)

        if self.only_new:
            papers = Paper.objects.filter(last_altmetric_update=None)
        elif self.once_per_day:
            # Update only papers, which were not updated today already
            today = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
            papers = Paper.objects.filter(Q(last_altmetric_update__lt=today) | Q(last_altmetric_update=None))
        else:
            papers = Paper.objects.all()

        sorted_papers = papers.order_by(F('last_altmetric_update').asc(nulls_first=True))

        if not self.update_all:
            sorted_papers = sorted_papers[:self.max_count]

        self.log(f"Update Altmetric data of {sorted_papers.count()} papers")

        n_errors = 0
        for paper in self.progress(sorted_papers):
            try:
                altmetric_update.update(paper)
            except (AltmetricException, AltmetricHTTPException) as ex:
                self.log(f"Error at paper {paper.doi}: {ex}")
                n_errors += 1
            if n_errors >= self.MAX_ERRORS:
                break

        if n_errors > 0:
            raise Exception("Failed to update all Altmetric scores")
