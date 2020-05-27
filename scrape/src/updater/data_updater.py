from datetime import timedelta
from time import sleep
from timeit import default_timer as timer

from data.models import Author, Category, DataSource, Paper, PaperData, PaperHost
from django.db import transaction
from django.db.models import F
from django.db.utils import DataError as DjangoDataError, IntegrityError
from django.utils import timezone

from src.pdf_extractor import PdfExtractError, PdfExtractor
from src.static_functions import covid_related


class UpdateException(Exception):
    def __init__(self, msg):
        self.msg = msg

    def __str__(self):
        return self.msg

    def __repr__(self):
        return self.msg


class DifferentDataSourceError(UpdateException):
    pass


class MissingDataError(UpdateException):
    pass


class SkipArticle(UpdateException):
    pass


class DataError(UpdateException):
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

    def extract_authors(self):
        return []

    @property
    def data_source(self):
        raise NotImplementedError

    @property
    def paperhost_name(self):
        raise NotImplementedError

    @property
    def paperhost_url(self):
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
        raise NotImplementedError

    @property
    def is_preprint(self):
        raise NotImplementedError

    @property
    def category_name(self):
        return None

    @staticmethod
    def _update_pdf_data(db_article, extract_image=True, extract_content=True):
        if not extract_image and not extract_content:
            return
        if not db_article.pdf_url:
            return

        sleep(3)
        pdf_extractor = PdfExtractor(db_article.pdf_url)

        if extract_image:
            image = pdf_extractor.extract_image()
            if image:
                db_article.add_preview_image(image)

        if extract_content:
            content = pdf_extractor.extract_contents()
            if content:
                if db_article.data:
                    db_article.data.content = content
                else:
                    db_content = PaperData.objects.create(content=content)
                    db_article.data = db_content

    def update_db(self, update_existing, pdf_content, pdf_image):
        doi = self.doi
        title = self.title
        paperhost_name = self.paperhost_name

        if not doi:
            raise MissingDataError("Couldn't extract doi")
        if not title:
            raise MissingDataError("Couldn't extract title")
        if not paperhost_name:
            raise MissingDataError("Couldn't extract paperhost")

        with transaction.atomic():
            try:
                db_article = Paper.objects.get(doi=doi)
                if db_article.data_source_value and DataSource(db_article.data_source_value).priority < self.data_source.priority:
                    raise DifferentDataSourceError(f"Article already tracked by {db_article.data_source_value.name}")
                elif not update_existing and DataSource(db_article.data_source_value).priority == self.data_source.priority:
                    raise SkipArticle("Article already in database")
                created = False
            except Paper.DoesNotExist:
                db_article = Paper(doi=doi)
                created = True

            db_article.title = title
            db_article.abstract = self.abstract
            db_article.data_source_value = self.data_source

            db_article.host, _ = PaperHost.objects.get_or_create(name=paperhost_name)
            if self.paperhost_url:
                db_article.host.url = self.paperhost_url

            db_article.published_at = self.published_at
            db_article.url = self.url
            db_article.pdf_url = self.pdf_url
            db_article.is_preprint = self.is_preprint

            db_article.save()

            try:
                authors = self.extract_authors()
            except AttributeError:
                raise MissingDataError("Couldn't extract authors, error in HTML soup")

            if len(authors) > 0:
                db_article.authors.clear()
            for author in authors:
                try:
                    db_author, _ = Author.objects.get_or_create(
                        first_name=author[1],
                        last_name=author[0],
                    )
                    db_article.authors.add(db_author)
                except DjangoDataError as ex:
                    raise DataError(f"Author {author[1]} {author[0]}: {ex}")

            if self.category_name:
                db_article.category, _ = Category.objects.get_or_create(name=self.category_name)

            if pdf_content or pdf_image:
                self._update_pdf_data(db_article, extract_image=pdf_image, extract_content=pdf_content)
            db_article.version = self.version
            db_article.covid_related = covid_related(db_article=db_article)
            db_article.last_scrape = timezone.now()
            db_article.save()
        return db_article, created


class DataUpdater(object):
    def __init__(self, log=print):
        self.log = log

        self.n_errors = 0
        self.n_skipped = 0
        self.n_already_tracked = 0
        self.n_success = 0

    @property
    def data_source(self):
        raise NotImplementedError

    def _get_data_points(self):
        raise NotImplementedError

    def _get_data_point(self, doi):
        raise NotImplementedError

    def _count(self):
        raise NotImplementedError

    def get_or_create_db_article(self, datapoint, pdf_content, pdf_image, update_existing):
        try:
            db_article, created = datapoint.update_db(update_existing=update_existing, pdf_content=pdf_content,
                                                      pdf_image=pdf_image)
            self.log(f"Updated/Created {datapoint.doi}")
            self.n_success += 1
            return db_article, created
        except MissingDataError as ex:
            id = datapoint.doi if datapoint.doi else f"\"{datapoint.title}\""
            self.log(f"Error: {id}: {ex.msg}")
            self.n_errors += 1
        except SkipArticle as ex:
            self.log(f"Skip: {datapoint.doi}: {ex.msg}")
            self.n_skipped += 1
        except DifferentDataSourceError as ex:
            self.log(f"Skip: {datapoint.doi}: {ex.msg}")
            self.n_already_tracked += 1
        except (IntegrityError, DjangoDataError, PdfExtractError, DataError) as ex:
            self.log(f"Error: {datapoint.doi}: {ex}")
            self.n_errors += 1
        return None, None

    def get_new_data(self, pdf_content=True, pdf_image=True):
        self.n_errors = 0
        self.n_skipped = 0
        self.n_already_tracked = 0
        self.n_success = 0

        total = self._count()
        self.log(f"Check {total} publications")

        start = timer()

        for i, data_point in enumerate(self._get_data_points()):
            if i % 100 == 0:
                self.log(f"Progress: {i}/{total}")
            self.get_or_create_db_article(data_point, pdf_content=pdf_content, pdf_image=pdf_image, update_existing=False)

        end = timer()
        elapsed_time = timedelta(seconds=end - start)
        self.log(f"Time (total): {elapsed_time}")
        total_handled = self.n_success + self.n_errors
        if total_handled > 0:
            self.log(f"Time (per Record): {elapsed_time / total_handled}")
        self.log(f"Created: {self.n_success}")
        self.log(f"Skipped: {self.n_skipped}")
        self.log(f"Errors: {self.n_errors}")
        self.log(f"Tracked by other source: {self.n_already_tracked}")

    def update_existing_data(self, count=None, pdf_content=True, pdf_image=True):
        self.n_errors = 0
        self.n_skipped = 0
        self.n_already_tracked = 0
        self.n_success = 0

        total = self._count()

        if count is None:
            count = total

        self.log(f"Update {count} existing articles")

        start = timer()

        filtered_articles = Paper.objects.all().filter(data_source__name=self.data_source).order_by(
            F('last_scrape').asc(nulls_first=True))[:count]
        for article in filtered_articles:
            data_point = self._get_data_point(doi=article.doi)
            if data_point:
                self.get_or_create_db_article(data_point, update_existing=True, pdf_content=pdf_content, pdf_image=pdf_image)

        end = timer()
        elapsed_time = timedelta(seconds=end - start)
        self.log(f"Time (total): {elapsed_time}")
        total_handled = self.n_success + self.n_errors
        if total_handled > 0:
            self.log(f"Time (per Record): {elapsed_time / total_handled}")
        self.log(f"Updated: {self.n_success}")
        self.log(f"Skipped: {self.n_skipped}")
        self.log(f"Errors: {self.n_errors}")
        self.log(f"Tracked by other source: {self.n_already_tracked}")