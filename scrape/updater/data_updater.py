from django.db import transaction
from django.db.utils import IntegrityError, DataError as DjangoDataError
from django.utils import timezone
from datetime import timedelta, date

from data.models import Author, Category, Paper, PaperHost, DataSource, PaperData
from django.core.files.uploadedfile import InMemoryUploadedFile
from scrape.pdf_extractor import PdfExtractor, PdfExtractError
from timeit import default_timer as timer

from scrape.static_functions import sanitize_doi, covid_related
from scrape.updater.update_error import UpdateError


class DifferentDataSourceError(UpdateError):
    pass


class MissingDataError(UpdateError):
    pass


class SkipArticle(UpdateError):
    pass


class DataError(UpdateError):
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

    def extract_content(self):
        self._setup_pdf_extractor()
        return self._pdf_extractor.extract_contents()

    def extract_preview_image(self):
        self._setup_pdf_extractor()
        return self._pdf_extractor.extract_image()

    @property
    def data_source_name(self):
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

        pdf_error = None
        with transaction.atomic():
            datasource, _ = DataSource.objects.get_or_create(name=self.data_source_name)

            try:
                db_article = Paper.objects.get(doi=doi)
                if db_article.data_source and db_article.data_source.priority < datasource.priority:
                    raise DifferentDataSourceError(f"Article already tracked by {db_article.data_source.name}")
                elif not update_existing and db_article.data_source.priority == datasource.priority:
                    raise SkipArticle("Article already in database")
                created = False
            except Paper.DoesNotExist:
                db_article = Paper(doi=doi)
                created = True

            db_article.title = title
            db_article.abstract = self.abstract
            db_article.data_source = datasource

            db_article.host, _ = PaperHost.objects.get_or_create(name=paperhost_name)
            if self.paperhost_url:
                db_article.host.url = self.paperhost_url

            db_article.published_at = self.published_at
            db_article.url = self.url
            db_article.pdf_url = self.pdf_url
            db_article.is_preprint = self.is_preprint

            db_article.save()

            if self.category_name:
                db_article.category, _ = Category.objects.get_or_create(name=self.category_name)

            try:
                if pdf_content:
                    content = self.extract_content()
                    if content:
                        if db_article.data:
                            db_article.data.content = content
                        else:
                            db_content = PaperData.objects.create(content=content)
                            db_article.data = db_content
            except PdfExtractError as ex:
                pdf_error = ex

            try:
                if pdf_image:
                    preview_image = self.extract_preview_image()
                    if preview_image:
                        img_name = sanitize_doi(db_article.doi) + ".jpg"
                        db_article.preview_image.save(
                            img_name, InMemoryUploadedFile(preview_image, None, img_name, 'image/jpeg', preview_image.tell, None)
                        )
            except PdfExtractError as ex:
                pdf_error = ex


            db_article.version = self.version
            db_article.covid_related = covid_related(db_article=db_article)


            try:
                authors = self.extract_authors()
            except AttributeError:
                raise MissingDataError("Couldn't extract authors, error in HTML soup")

            if db_article.covid_related:
                if len(authors) > 0:
                    db_article.authors.clear()
                for author in authors:
                    try:
                        db_author, _ = Author.objects.get_or_create(
                            first_name=author[1],
                            last_name=author[0],
                            data_source=db_article.data_source,
                        )
                        db_article.authors.add(db_author)
                    except DjangoDataError as ex:
                        raise DataError(f"Author {author[1]} {author[0]}: {ex}")

                db_article.last_scrape = timezone.now()
                db_article.save()
            else:
                raise SkipArticle("Not covid Related")
        if pdf_error:
            raise pdf_error
        return db_article, created


class DataUpdater(object):
    def __init__(self, log=print):
        self.log = log

        self.n_errors = 0
        self.n_skipped = 0
        self.n_already_tracked = 0
        self.n_success = 0

    @property
    def data_source_name(self):
        raise NotImplementedError

    def _preprocess(self):
        pass

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
        except (IntegrityError, DjangoDataError, DataError) as ex:
            self.log(f"Error: {datapoint.doi}: {ex}")
            self.n_errors += 1
        except PdfExtractError as ex:
            self.log(f"PDF Error: {datapoint.doi}: {ex}")
            self.n_success += 1
        return None, None

    def get_new_data(self, pdf_content=True, pdf_image=True):
        self.n_errors = 0
        self.n_skipped = 0
        self.n_already_tracked = 0
        self.n_success = 0

        self._preprocess()

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

        self._preprocess()

        total = self._count()

        if count is None:
            count = total

        self.log(f"Update {count} existing articles")

        start = timer()

        filtered_articles = Paper.objects.all().filter(data_source__name=self.data_source_name).order_by(
            'last_scrape')[:count]
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