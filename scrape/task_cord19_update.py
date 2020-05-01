from scrape.updater.cord19_update import update_cord19_data
from tasks import register_task, Runnable


@register_task
class Cord19Downloader(Runnable):
    @staticmethod
    def task_name():
        return "download-cord19"

    def __init__(self, *args, **kwargs):
        super(Cord19Downloader, self).__init__(*args, **kwargs)

    def run(self):
        update_cord19_data()
