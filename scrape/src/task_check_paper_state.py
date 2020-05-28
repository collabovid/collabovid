from data.models import Paper
from tasks.definitions import register_task, Runnable


@register_task
class CheckPaperStateTask(Runnable):
    @staticmethod
    def task_name():
        return "check-paper-states-automatically"

    @staticmethod
    def description():
        return (
            "Automatically check the paper state of unknown and automatically accepted papers."
        )

    def __init__(self, *args, **kwargs):
        super(CheckPaperStateTask, self).__init__(*args, **kwargs)

    def run(self):
        papers = Paper.objects.all()
        for paper in papers:
            paper.automatic_state_check(save=True)
