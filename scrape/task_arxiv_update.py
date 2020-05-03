from scrape.updater.arxiv_update import ArxivUpdater
from tasks.definitions import register_task, Runnable


@register_task
class ArxivUpdateTask(Runnable):
    @staticmethod
    def task_name():
        return "update-arxiv"

    def __init__(self, *args, **kwargs):
        super(ArxivUpdateTask, self).__init__(*args, **kwargs)

    def run(self):
        updater = ArxivUpdater(log=self.log)
        updater.update()
