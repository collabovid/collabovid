from scrape.updater.cord19_update import Cord19Updater
from tasks import register_task, Runnable


@register_task
class Cord19UpdateTask(Runnable):
    @staticmethod
    def task_name():
        return "update-cord19"

    def __init__(self, *args, **kwargs):
        super(Cord19UpdateTask, self).__init__(*args, **kwargs)

    def run(self):
        updater = Cord19Updater(log=self.log)
        updater.update()
