import functools
import re

from django.db import transaction
from django.utils import timezone
from datetime import timedelta, date

from data.models import Author, Category, Paper, PaperHost, DataSource, Journal, PaperData
from django.core.files.uploadedfile import InMemoryUploadedFile
from scrape.pdf_extractor import PdfExtractor, PdfDownloadError
from timeit import default_timer as timer

from multiprocessing import Pool as ThreadPool


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

    def extract_authors(self):
        return []

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

    @property
    def pubmed_id(self):
        return None

    @property
    def pmcid(self):
        return None

    @staticmethod
    def _covid_related(db_article):
        if db_article.published_at and db_article.published_at < date(year=2019, month=12, day=1):
            return False

        _COVID19_KEYWORDS = r'(corona.?virus|(^|\s)corona(\s|$)|covid.?19|(^|\s)covid(\s|$)|sars.?cov.?2|2019.?ncov)'

        return bool(re.search(_COVID19_KEYWORDS, db_article.title, re.IGNORECASE)) \
            or bool(re.search(_COVID19_KEYWORDS, db_article.abstract, re.IGNORECASE)) \
            or bool((db_article.data and re.search(_COVID19_KEYWORDS, db_article.data.content, re.IGNORECASE)))

    def update_db(self, update_existing=True):
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
            datasource, _ = DataSource.objects.get_or_create(name=self.data_source_name)

            try:
                db_article = Paper.objects.get(doi=doi)
                if db_article.data_source.priority < datasource.priority:
                    raise DifferentDataSourceError(f"Article already tracked by {db_article.data_source.name}")
                elif not update_existing and db_article.data_source.priority == datasource.priority:
                    raise SkipArticle("Article already in database")
            except Paper.DoesNotExist:
                db_article = Paper(doi=doi)

            db_article.title = title
            db_article.abstract = self.abstract
            db_article.data_source = datasource

            db_article.host, _ = PaperHost.objects.get_or_create(name=paperhost_name)
            if self.paperhost_url:
                db_article.host.url = self.paperhost_url

            if self.journal:
                db_article.journal, _ = Journal.objects.get_or_create(name=self.journal)
            db_article.published_at = self.published_at
            db_article.url = self.url
            db_article.pdf_url = self.pdf_url
            db_article.is_preprint = self.is_preprint
            db_article.pmcid = self.pmcid
            db_article.pubmed_id = self.pubmed_id

            db_article.save()

            try:
                authors = self.extract_authors()
            except AttributeError:
                raise MissingDataError("Couldn't extract authors, error in HTML soup")

            if len(authors) > 0:
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

            db_article.version = self.version
            db_article.covid_related = self._covid_related(db_article=db_article)
            db_article.last_scrape = timezone.now()
            db_article.save()
        return db_article


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

    def _get_data_points(self):
        raise NotImplementedError

    def _get_data_point(self, doi):
        raise NotImplementedError

    def _count(self):
        raise NotImplementedError

    @staticmethod
    def _sanitize_doi(doi):
        return doi.replace("/", "_").replace(".", "_").replace(",", "_").replace(":", "_")

    def _extract_pdf_data(self, db_articles):
        pdf_extractor = PdfExtractor([x.pdf_url for x in db_articles if x.pdf_url])
        images = pdf_extractor.extract_images()
        contents = pdf_extractor.extract_contents()

        for article, image, content in zip([x for x in db_articles if x.pdf_url], images, contents):
            if image:
                img_name = self._sanitize_doi(article.doi) + ".jpg"
                article.preview_image.save(img_name, InMemoryUploadedFile(
                    image,  # file
                    None,  # field_name
                    img_name,  # file name
                    'image/jpeg',  # content_type
                    image.tell,  # size
                    None))

            if content:
                if article.data:
                    article.data.content = content
                else:
                    db_content = PaperData.objects.create(content=content)
                    article.data = db_content

    def _update_data(self, data_point, update_existing=True):
        try:
            db_article = data_point.update_db(update_existing=update_existing)
            self.log(f"Updated/Created {data_point.doi}")
            self.n_success += 1
            return db_article
        except MissingDataError as ex:
            id = data_point.doi if data_point.doi else f"\"{data_point.title}\""
            self.log(f"Error: {id}: {ex.msg}")
            self.n_errors += 1
        except SkipArticle as ex:
            #self.log(f"Skip: {data_point.doi}: {ex.msg}")
            self.n_skipped += 1
        except DifferentDataSourceError as ex:
            #self.log(f"Skip: {data_point.doi}: {ex.msg}")
            self.n_already_tracked += 1
        return None

    def update(self, max_count=None):
        self.n_errors = 0
        self.n_skipped = 0
        self.n_already_tracked = 0
        self.n_success = 0

        total = self._count()
        self.log(f"Check {total} publications")

        update_existing = max_count is None

        start = timer()

        chunk_size = 4
        article_buffer = []
        for i, data_point in enumerate(self._get_data_points()):
            if i % 100 == 0:
                self.log(f"Progress: {i}/{total}")
            db_article = self._update_data(data_point, update_existing=update_existing)
            if db_article:
                article_buffer.append(db_article)
            if len(article_buffer) == chunk_size:
                self._extract_pdf_data(article_buffer)
                for art in article_buffer:
                    art.save()
                article_buffer.clear()
        if len(article_buffer) > 0:
            self._extract_pdf_data(article_buffer)
            for art in article_buffer:
                art.save()
            article_buffer.clear()

        total_handled = self.n_success + self.n_errors
        if max_count and total_handled < max_count:
            self.log("Update existing articles")
            filtered_articles = Paper.objects.all().filter(data_source__name=self._data_source_name)
            update_articles = filtered_articles.order_by('last_scrape')[:max_count - total_handled]
            for article in update_articles:
                data_point = self._get_data_point(doi=article.doi)
                if data_point:
                    self._update_data(data_point, update_existing=True)

        end = timer()
        elapsed_time = timedelta(seconds=end-start)
        self.log(f"Time (total): {elapsed_time}")
        if total_handled > 0:
            self.log(f"Time (per Record): {elapsed_time / total_handled}")
        self.log(f"Updated/Created: {self.n_success}")
        self.log(f"Skipped: {self.n_skipped}")
        self.log(f"Errors: {self.n_errors}")
        self.log(f"Tracked by other source: {self.n_already_tracked}")
