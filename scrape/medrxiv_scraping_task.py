from scrape.scraper.medrxiv_scraper import scrape_articles, delete_revoked_articles, update_articles
from tasks import register_task, Runnable


@register_task
class ArticleScraper(Runnable):
    @staticmethod
    def task_name():
        return "scrape-articles"

    def __init__(self, update_unknown_category=True, *args, **kwargs):
        super(ArticleScraper, self).__init__(*args, **kwargs)
        self._update_unknown_category = update_unknown_category

    def run(self):
        scrape_articles(self._update_unknown_category, self.log)


@register_task
class ArticleUpdater(Runnable):
    @staticmethod
    def task_name():
        return "update-articles"

    def __init__(self, count=200, *args, **kwargs):
        super(ArticleUpdater, self).__init__(*args, **kwargs)
        self._count = count

    def run(self):
        update_articles(self._count, self.log)


@register_task
class DeleteRevokedArticlesTask(Runnable):
    @staticmethod
    def task_name():
        return "delete-revoked-articles"

    def run(self):
        delete_revoked_articles(self.log)