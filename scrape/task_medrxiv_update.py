from scrape.updater.medrxiv_update import MedrxivUpdater
from tasks.definitions import register_task, Runnable


@register_task
class MedrxivUpdateTask(Runnable):
    @staticmethod
    def task_name():
        return "update-medbiorxiv"

    def __init__(self, update_unknown_category=True, *args, **kwargs):
        super(MedrxivUpdateTask, self).__init__(*args, **kwargs)
        self._update_unknown_category = update_unknown_category

    def run(self):
        updater = MedrxivUpdater(log=self.log)
        updater.update(pdf_content=True)
        #scrape_articles(self._update_unknown_category, self.log) # TODO: unknown_categories
