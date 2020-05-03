import re

from django.utils import timezone
from datetime import timedelta, date

from data.models import Author, Category, Paper, PaperHost, DataSource, Journal, PaperData
from django.core.files.uploadedfile import InMemoryUploadedFile
from scrape.pdf_extractor import PdfExtractor, PdfDownloadError
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
    def __init__(self):
        self._pdf_extractor = None

    def _setup_pdf_extractor(self):
        if not self._pdf_extractor:
            self._pdf_extractor = PdfExtractor(self.pdf_url)

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
    def extract_authors(self):
        return []

    def extract_content(self):
        if self.pdf_url:
            self._setup_pdf_extractor()
            try:
                return self._pdf_extractor.extract_content()
            except PdfDownloadError:
                return None
        else:
            return None

    def extract_image(self):
        if self.pdf_url:
            try:
                self._setup_pdf_extractor()
                return self._pdf_extractor.extract_image()
            except PdfDownloadError:
                return None
        else:
            return None

    @property
    def data_source_name(self):
        raise NotImplementedError

    @property
    def data_source_priority(self):
        raise NotImplementedError

    @property
    def paperhost_name(self):
        raise NotImplementedError

    @property
    def paperhost_url(self):
        raise NotImplementedError

    @property
    def journal(self):
        return None

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
        raise NotImplementedError

    @property
    def is_preprint(self):
        raise NotImplementedError

    @property
    def category_name(self):
        return None

    @staticmethod
    def _covid_related(db_article):
        if db_article.published_at and db_article.published_at < date(year=2019, month=12, day=1):
            return False

        _COVID19_KEYWORDS = r'(corona.?virus|(^|\s)corona(\s|$)|covid.?19|(^|\s)covid(\s|$)|sars.?cov.?2|2019.?ncov)'

        return bool(re.search(_COVID19_KEYWORDS, db_article.title, re.IGNORECASE)) \
            or bool(re.search(_COVID19_KEYWORDS, db_article.abstract, re.IGNORECASE)) \
            or bool((db_article.data and re.search(_COVID19_KEYWORDS, db_article.data.content, re.IGNORECASE)))

    @staticmethod
    def _sanitize_doi(doi):
        return doi.replace("/", "_").replace(".", "_").replace(",", "_").replace(":", "_")

    def update_db(self, update_existing=True):
        doi = self.doi
        title = self.title
        paperhost_name = self.paperhost_name

        if not doi:
            raise MissingDataError("Couldn't extract doi")
        if not title:
            raise MissingDataError("Couldn't extrat title")
        if not paperhost_name:
            raise MissingDataError("Couldn't extract paperhost")

        try:
            db_article = Paper.objects.get(doi=doi)
            if not update_existing:
                raise SkipArticle("Article already in database")
        except Paper.DoesNotExist:
            db_article = Paper(doi=doi)

        datasource, _ = DataSource.objects.get_or_create(name=self.data_source_name)
        if db_article.data_source and db_article.data_source.priority < datasource.priority:
            raise DifferentDataSourceError(f"Article already tracked by {db_article.data_source.name}")

        db_article.title = title
        db_article.abstract = self.abstract
        db_article.data_source = datasource
        db_article.host, _ = PaperHost.objects.get_or_create(name=self.paperhost_name,
                                                             url=self.paperhost_url)
        if self.journal:
            db_article.journal, _ = Journal.objects.get_or_create(name=self.journal)
        db_article.published_at = self.published_at
        db_article.url = self.url
        db_article.pdf_url = self.pdf_url
        db_article.is_preprint = self.is_preprint

        db_article.save()
        authors = self.extract_authors
        if len(self.extract_authors) > 0:
            db_article.authors.clear()
        for author in authors:
            db_author, _ = Author.objects.get_or_create(
                first_name=author[1],
                last_name=author[0],
                data_source=db_article.data_source,
            )
            db_article.authors.add(db_author)

        if self.category_name:
            db_article.category, _ = Category.objects.get_or_create(name=self.category_name)

        if self.version != db_article.version:
            content = self.extract_content()
            if content:
                if db_article.data:
                    db_article.data.content = content
                else:
                    db_content = PaperData.objects.create(content=content)
                    db_article.data = db_content

            preview_image = self.extract_image()
            if preview_image:
                img_name = self._sanitize_doi(self.doi) + ".jpg"
                db_article.preview_image.save(img_name, InMemoryUploadedFile(
                    preview_image,  # file
                    None,  # field_name
                    img_name,  # file name
                    'image/jpeg',  # content_type
                    preview_image.tell,  # size
                    None))

        db_article.version = self.version
        db_article.covid_related = self._covid_related(db_article=db_article)
        db_article.last_scrape = timezone.now()
        db_article.save()
        return True


class DataUpdater(object):
    def __init__(self, log=print):
        self.log = log

        self.n_errors = 0
        self.n_skipped = 0
        self.n_already_tracked = 0
        self.n_success = 0

    @property
    def _data_source_name(self):
        raise NotImplementedError

    @property
    def _data_points(self):
        raise NotImplementedError

    def _get_data_point(self, doi):
        raise NotImplementedError

    def _update_data(self, data_point, update_existing=True):
        try:
            data_point.update_db(update_existing=update_existing)
            self.log(f"Updated/Created {data_point.doi}")
            self.n_success += 1
        except MissingDataError as ex:
            id = data_point.doi if data_point.doi else f"\"{data_point.title}\""
            self.log(f"Error: {id}: {ex.msg}")
            self.n_errors += 1
        except SkipArticle as ex:
            self.log(f"Sip: {data_point.doi}: {ex.msg}")
            self.n_skipped += 1
            pass
        except DifferentDataSourceError as ex:
            self.log(f"{data_point.doi}: {ex.msg}")
            self.n_already_tracked += 1

    def update(self, max_count=None):
        self.n_errors = 0
        self.n_skipped = 0
        self.n_already_tracked = 0
        self.n_success = 0

        update_existing = not max_count

        start = timer()
        for data_point in self._data_points:
            self._update_data(data_point, update_existing=update_existing)

        total = self.n_success + self.n_errors
        if max_count and total < max_count:
            filtered_articles = Paper.objects.all().filter(data_source__name=self._data_source_name)
            update_articles = filtered_articles.order_by('last_scrape')[:max_count - total]
            for article in update_articles:
                data_point = self._get_data_point(doi=article.doi)
                if data_point:
                    self._update_data(data_point, update_existing=True)

        end = timer()
        self.log(f"Finished: {timedelta(seconds=end-start)}")
        self.log(f"Created: {self.n_success}")
        self.log(f"Skipped: {self.n_skipped}")
        self.log(f"Errors: {self.n_errors}")
        self.log(f"Tracked by other source: {self.n_already_tracked}")
