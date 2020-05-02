from scrape.updater.medrxiv_update import MedrxivUpdater
from tasks import register_task, Runnable


@register_task
class MedrxivUpdateTask(Runnable):
    @staticmethod
    def task_name():
        return "update-medbiorxiv"

    def __init__(self, update_unknown_category=True, *args, **kwargs):
        super(MedrxivUpdateTask, self).__init__(*args, **kwargs)
        self._update_unknown_category = update_unknown_category

    def run(self):
        updater = MedrxivUpdater()
        updater.update()
        #scrape_articles(self._update_unknown_category, self.log) # TODO: unknown_categories


# @register_task
# class ArticleUpdater(Runnable):
#     @staticmethod
#     def task_name():
#         return "update-articles"
#
#     def __init__(self, count=200, *args, **kwargs):
#         super(ArticleUpdater, self).__init__(*args, **kwargs)
#         self._count = count
#
#     def run(self):
#         update_articles(self._count, self.log)
#
#
# @register_task
# class DeleteRevokedArticlesTask(Runnable):
#     @staticmethod
#     def task_name():
#         return "delete-revoked-articles"
#
#     def run(self):
#         delete_revoked_articles(self.log)