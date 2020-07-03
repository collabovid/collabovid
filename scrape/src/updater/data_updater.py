from datetime import timedelta
from time import sleep
from timeit import default_timer as timer

from data.models import Author, DataSource, Journal, Paper, PaperData, PaperHost
from django.db import transaction
from django.db.models import F
from django.db.utils import DataError as DjangoDataError, IntegrityError
from django.utils import timezone
from src.pdf_extractor import PdfExtractError, PdfFromUrlExtractor
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


class NotCovidRelatedError(UpdateException):
    pass


class UpdateStatistics:
    """
    Class that holds statistics for the update process.
    """
    def __init__(self):
        self.n_errors = 0
        self.n_skipped = 0
        self.n_already_tracked = 0
        self.n_success = 0
        self.n_missing_datapoints = 0

        self.authors_deleted = 0
        self.journals_deleted = 0

        self.start_time = None
        self.end_time = None

    def start(self):
        self.start_time = timer()

    def stop(self):
        self.end_time = timer()

    def __str__(self):
        s = []

        elapsed_time = timedelta(seconds=self.end_time - self.start_time)
        s.append(f"Time (total): {elapsed_time}")
        total_handled = self.n_success + self.n_errors
        if total_handled > 0:
            s.append(f"Time (per Record): {elapsed_time / total_handled}")
        s.append(f"Created/Updated: {self.n_success}")
        s.append(f"Skipped: {self.n_skipped}")
        s.append(f"Errors: {self.n_errors}")
        s.append(f"Missing Datapoints: {self.n_missing_datapoints}")
        s.append(f"Tracked by other source: {self.n_already_tracked}")
        s.append(f"Deleted Authors: {self.authors_deleted}")
        s.append(f"Deleted Journals: {self.journals_deleted}")

        return '\n'.join(s)


class ArticleDataPoint(object):
    def __init__(self):
        self._pdf_extractor = None

    def _setup_pdf_extractor(self):
        if not self._pdf_extractor:
            self._pdf_extractor = PdfFromUrlExtractor(self.pdf_url)

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
    def pubmed_id(self):
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
    def journal(self):
        return None

    @property
    def update_timestamp(self):
        return None

    @staticmethod
    def update_pdf_data(db_article, extract_image=True, extract_content=True):
        if not extract_image and not extract_content:
            return
        if not db_article.pdf_url:
            return

        sleep(3)
        pdf_extractor = PdfFromUrlExtractor(db_article.pdf_url)

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
        abstract = self.abstract
        published_at = self.published_at

        if not doi:
            raise MissingDataError("Couldn't extract doi")
        if not title:
            raise MissingDataError("Couldn't extract title")
        if len(title) > Paper.max_length("title"):
            raise DataError(f"Title exceeds maximum length: {title}")
        if not paperhost_name:
            raise MissingDataError("Couldn't extract paperhost")
        if not abstract:
            raise MissingDataError("Couldn't extract abstract")
        if not published_at:
            raise MissingDataError("Couldn't extract date")

        with transaction.atomic():
            try:
                db_article = Paper.objects.get(doi=doi)
                if DataSource.compare(db_article.data_source_value, self.data_source) > 0:
                    raise DifferentDataSourceError(
                        f"Article already tracked by {DataSource(db_article.data_source_value).name}")
                elif not update_existing and DataSource.compare(db_article.data_source_value, self.data_source) == 0:
                    raise SkipArticle("Article already in database")
                created = False
            except Paper.DoesNotExist:
                db_article = Paper(doi=doi)
                created = True

            db_article.title = title
            db_article.abstract = abstract
            db_article.data_source_value = self.data_source
            db_article.published_at = published_at

            db_article.covid_related = covid_related(db_article=db_article)
            if self.data_source.check_covid_related and not db_article.covid_related:
                raise NotCovidRelatedError("Article not covid related.")

            db_article.host, _ = PaperHost.objects.get_or_create(name=paperhost_name)
            if self.paperhost_url:
                db_article.host.url = self.paperhost_url

            db_article.url = self.url
            db_article.pdf_url = self.pdf_url
            db_article.is_preprint = self.is_preprint
            db_article.pubmed_id = self.pubmed_id
            db_article.save()

            authors = self.extract_authors()

            if len(authors) == 0:
                raise MissingDataError("Found no authors")

            db_article.authors.clear()
            for author in authors:
                try:
                    if (
                            (author[1] and len(author[1]) > Author.max_length("first_name")) or
                            (author[0] and len(author[0]) > Author.max_length("last_name"))
                    ):
                        raise DataError(f"Author exceeds maximum length: {author}")

                    db_author, _ = Author.objects.get_or_create(
                        first_name=author[1],
                        last_name=author[0],
                    )
                    db_article.authors.add(db_author)
                except DjangoDataError as ex:
                    raise DataError(f"Author {author[1]} {author[0]}: {ex}")

            if self.journal:
                db_article.journal, _ = Journal.objects.get_or_create(
                    name=self.journal[:Journal.max_length("name")]
                )

            if pdf_content or pdf_image:
                self.update_pdf_data(db_article, extract_image=pdf_image, extract_content=pdf_content)
            db_article.version = self.version

            db_article.last_scrape = timezone.now()

            db_article.categories.clear()
            db_article.save()
        return db_article, created


class DataUpdater(object):
    def __init__(self, log=print):
        self.log = log
        self.statistics = UpdateStatistics()

    @property
    def data_source(self):
        raise NotImplementedError

    def _get_data_points(self):
        raise NotImplementedError

    def _get_data_point(self, doi):
        raise NotImplementedError

    def _count(self):
        raise NotImplementedError

    @staticmethod
    def set_last_scrape(datapoint):
        """
        Set the current time as last_scrape time.
        Needs to be done if articles should be updated and now contain data errors.
        Otherwise, we would try to update these articles over and over.
        """
        if datapoint.doi:
            try:
                db_article = Paper.objects.get(doi=datapoint.doi)
                db_article.last_scrape = timezone.now()
                db_article.save()
            except Paper.DoesNotExist:
                pass

    def get_or_create_db_article(self, datapoint, pdf_content, pdf_image, update_existing):
        try:
            db_article, created = datapoint.update_db(update_existing=update_existing, pdf_content=pdf_content,
                                                      pdf_image=pdf_image)
            self.log(f"Updated/Created {datapoint.doi}")
            self.statistics.n_success += 1
            return db_article, created
        except MissingDataError as ex:
            id = datapoint.doi if datapoint.doi else f"\"{datapoint.title}\""
            if update_existing:
                DataUpdater.set_last_scrape(datapoint)
            self.log(f"Error: {id}: {ex.msg}")
            self.statistics.n_errors += 1
        except SkipArticle as ex:
            self.log(f"Skip: {datapoint.doi}: {ex.msg}")
            self.statistics.n_skipped += 1
        except NotCovidRelatedError as ex:
            if update_existing:
                DataUpdater.set_last_scrape(datapoint)
            self.log(f"Skip: {datapoint.doi}: {ex.msg}")
            self.statistics.n_skipped += 1
        except DifferentDataSourceError as ex:
            self.log(f"Skip: {datapoint.doi}: {ex.msg}")
            self.statistics.n_already_tracked += 1
        except (IntegrityError, DjangoDataError, PdfExtractError, DataError) as ex:
            if update_existing:
                DataUpdater.set_last_scrape(datapoint)
            self.log(f"Error: {datapoint.doi}: {ex}")
            self.statistics.n_errors += 1
        return None, None

    def get_new_data(self, pdf_content=True, pdf_image=True, progress=None):
        self.statistics = UpdateStatistics()
        self.statistics.start()

        total = self._count()
        self.log(f"Check {total} publications")

        start = timer()
        iterator = progress(self._get_data_points(), length=total) if progress else self._get_data_points()

        for data_point in iterator:
            self.get_or_create_db_article(data_point, pdf_content=pdf_content, pdf_image=pdf_image,
                                          update_existing=False)

        self.log("Delete orphaned authors and journals")
        self.statistics.authors_deleted = Author.cleanup()
        self.statistics.journals_deleted = Journal.cleanup()

        self.statistics.stop()
        self.log(self.statistics)

    def update_existing_data(self, count=None, pdf_content=True, pdf_image=True, progress=None):
        """
        Updates the stored papers, starting with the one with the earliest last-scrape.
        Count is the total number of papers to update.
        """
        self.statistics = UpdateStatistics()
        self.statistics.start()

        total = self._count()

        if count is None:
            count = total

        self.log(f"Update {count} existing articles")

        filtered_articles = Paper.objects.all().filter(data_source_value=self.data_source).order_by(
            F('last_scrape').asc(nulls_first=True)
        )

        datapoints_completed = 0
        for article in filtered_articles:
            if count:
                if datapoints_completed >= count:
                    break
                if progress:
                    progress(int((datapoints_completed / count) * 100))
            data_point = self._get_data_point(doi=article.doi)
            if data_point:
                datapoints_completed += 1
                if data_point.update_timestamp and article.last_scrape > data_point.update_timestamp:
                    DataUpdater.set_last_scrape(data_point)
                    continue
                self.get_or_create_db_article(data_point, update_existing=True, pdf_content=pdf_content,
                                              pdf_image=pdf_image)
            else:
                self.log(f"Missing Data Point: {article.doi}")
                self.statistics.n_missing_datapoints += 1
        self.log("Delete orphaned authors and journals")
        self.statistics.authors_deleted = Author.cleanup()
        self.statistics.journals_deleted = Journal.cleanup()

        self.statistics.stop()
        self.log(self.statistics)
