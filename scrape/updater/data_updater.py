import re

from django.utils import timezone
from datetime import datetime, timedelta

from data.models import Paper, PaperHost, DataSource, Journal
from timeit import default_timer as timer


class UpdateException(Exception):
    def __init__(self, msg):
        self.msg = msg


class DifferentDataSourceError(UpdateException):
    pass


class MissingDataError(UpdateException):
    pass


class SkipArticle(UpdateException):
    pass


class ArticleDataPoint(object):
    @property
    def doi(self):
        raise NotImplementedError

    @property
    def title(self):
        raise NotImplementedError

    @property
    def abstract(self):
        return ''

    @property
    def authors(self):
        return []

    @property
    def content(self):
        return None

    @property
    def data_source(self):
        raise NotImplementedError

    @property
    def data_source_priority(self):
        raise NotImplementedError

    @property
    def paperhost(self):
        raise NotImplementedError

    @property
    def journal(self):
        raise NotImplementedError

    @property
    def published_at(self):
        return None

    @property
    def url(self):
        return None

    @property
    def pdf_url(self):
        return None

    @property
    def version(self):
        return 1

    @staticmethod
    def _covid_related(db_article):
        if db_article.published_at and db_article.published_at >= datetime(year=2019, month=12, day=1):
            _COVID19_KEYWORDS = r'(corona([ -]?virus)?|covid[ -]?19|sars[ -]?cov[ -]?2)'
        else:
            _COVID19_KEYWORDS = r'(covid[ -]?19|sars[ -]?cov[ -]?2)'

        return bool(re.search(_COVID19_KEYWORDS, db_article.title, re.IGNORECASE)) \
            or bool(re.search(_COVID19_KEYWORDS, db_article.abstract)) \
            or bool((db_article.data and re.search(_COVID19_KEYWORDS, db_article.data.content)))

    def update_db(self, update_existing=True):
        doi = self.doi
        title = self.title
        paperhost = self.paperhost

        if not doi:
            raise MissingDataError("Couldn't extract doi")
        if not title:
            raise MissingDataError("Couldn't extrat title")
        if not paperhost:
            raise MissingDataError("Couldn't extract paperhost")

        try:
            db_article = Paper.objects.get(doi=doi)
            if not update_existing:
                raise SkipArticle("Article already in database")
        except Paper.DoesNotExist:
            db_article = Paper(doi=doi)

        if db_article.data_source and db_article.data_source.priority < self.data_source_priority:
            raise DifferentDataSourceError(f"Article already tracked by {db_article.data_source.name}")

        db_article.title = title
        db_article.abstract = self.abstract
        db_article.data_source, _ = DataSource.objects.get_or_create(name=self.data_source)
        db_article.host, _ = PaperHost.objects.get_or_create(name=paperhost)
        if self.journal:
            db_article.journal, _ = Journal.objects.get_or_create(name=self.journal)
        db_article.published_at = self.published_at
        db_article.version = self.version
        db_article.url = self.url
        db_article.pdf_url = self.pdf_url

        db_article.save()
        if db_article.authors.count() > 0:
            db_article.authors.clear()
        db_article.authors.add(*self.authors)

        db_article.content = self.content
        db_article.covid_related = self._covid_related(db_article=db_article)
        db_article.last_scrape = timezone.now()
        db_article.save()
        return True


class DataUpdater(object):
    def __init__(self):
        self.n_errors = 0
        self.n_skipped = 0
        self.n_already_tracked = 0
        self.n_success = 0

    @property
    def _data_points(self):
        raise NotImplementedError

    def _get_data_point(self, doi):
        raise NotImplementedError

    def _update_data(self, data_point, update_existing=True, log=print):
        try:
            data_point.update_db(update_existing=update_existing)
            log(f"Updated {data_point.doi}")
            self.n_success += 1
        except MissingDataError as ex:
            id = data_point.doi if data_point.doi else data_point.title
            log(f"{id}: {ex.msg}")
            self.n_errors += 1
        except SkipArticle as ex:
            log(f"{data_point.doi}: {ex.msg}")
            self.n_skipped += 1
            pass
        except DifferentDataSourceError as ex:
            log(f"{data_point.doi}: {ex.msg}")
            self.n_already_tracked += 1

    def update(self, max_count=None, log=print):
        self.n_errors = 0
        self.n_skipped = 0
        self.n_already_tracked = 0
        self.n_success = 0

        update_existing = not max_count

        start = timer()
        for data_point in self._data_points:
            self._update_data(data_point, update_existing=update_existing, log=log)

        total = self.n_success + self.n_errors
        if max_count and total < max_count:
            update_articles = Paper.objects.all().order_by('last_scrape')[:max_count - total]  # TODO: test
            for article in update_articles:
                data_point = self._get_data_point(doi=article.doi)
                if data_point:
                    self._update_data(data_point, update_existing=True)

        end = timer()
        log(f"Finished: {timedelta(seconds=end-start)}")
        log(f"Errors: {self.n_errors}")
        log(f"Tracked by other source: {self.n_already_tracked}")
