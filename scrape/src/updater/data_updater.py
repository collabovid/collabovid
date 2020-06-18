import hashlib
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from time import sleep
from timeit import default_timer as timer
from typing import List, Optional, Tuple

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


class ArticleModifiedError(UpdateException):
    pass


class UpdateStatistics:
    def __init__(self):
        self.n_errors = 0
        self.n_skipped = 0
        self.n_already_tracked = 0
        self.n_created = 0
        self.n_updated = 0
        self.n_conflicts = 0

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
        total_handled = self.n_created + self.n_updated + self.n_errors
        if total_handled > 0:
            s.append(f"Time (per Record): {elapsed_time / total_handled}")
        s.append(f"Created: {self.n_created}")
        s.append(f"Updated: {self.n_updated}")
        s.append(f"Skipped: {self.n_skipped}")
        s.append(f"Errors: {self.n_errors}")
        s.append(f"Tracked by other source: {self.n_already_tracked}")
        s.append(f"Deleted Authors: {self.authors_deleted}")
        s.append(f"Deleted Journals: {self.journals_deleted}")

        return '\n'.join(s)


@dataclass
class ArticleDataPoint(object):
    doi: Optional[str] = None
    title: Optional[str] = None
    abstract: Optional[str] = None
    authors: List[Tuple[str, str]] = field(default_factory=list)
    datasource: Optional[str] = None
    paperhost_name: Optional[str] = None
    paperhost_url: Optional[str] = None
    pubmed_id: Optional[str] = None
    published_at: Optional[date] = None
    url: Optional[str] = None
    pdf_url: Optional[str] = None
    version: Optional[str] = None
    is_preprint: Optional[bool] = None
    journal: Optional[str] = None
    update_timestamp: Optional[datetime] = None

    def to_dict(self):
        return {
            'doi': self.doi,
            'title': self.title,
            'abstract': self.abstract,
            'authors': [f"{x[0]}; {x[1]}" for x in self.authors],
            'datasource': self.datasource,
            'paperhost_name': self.paperhost_name,
            'paperhost_url': self.paperhost_url,
            'pubmed_id': self.pubmed_id,
            'published_at': self.published_at,
            'url': self.url,
            'pdf_url': self.pdf_url,
            'version': self.version,
            'is_preprint': self.is_preprint,
            'journal': self.journal,
            'update_timestamp': self.update_timestamp,
        }

    def get_hash(self):
        """
        Return a hash, built from all intance variables.
        """
        hash = hashlib.md5()

        def update_if_not_none(value: str):
            if value is not None:
                hash.update(value.encode('utf-8'))

        update_if_not_none(self.doi)
        update_if_not_none(self.title)
        update_if_not_none(self.abstract)
        for lastname, firstname in self.authors:
            update_if_not_none(lastname)
            update_if_not_none(firstname)
        update_if_not_none(self.datasource)
        update_if_not_none(self.paperhost_name)
        update_if_not_none(self.paperhost_url)
        update_if_not_none(self.pubmed_id)
        update_if_not_none(self.published_at.strftime("%Y%m%d") if self.published_at else None)
        update_if_not_none(self.url)
        update_if_not_none(self.pdf_url)
        update_if_not_none(self.version)
        update_if_not_none(str(self.is_preprint))
        update_if_not_none(self.journal)
        update_if_not_none(self.update_timestamp.strftime("%Y%m%d%H%M%S") if self.update_timestamp else None)

        return hash.digest()

    def check_integrity_constraints(self):
        if not self.doi:
            raise MissingDataError("Couldn't extract doi")
        if not self.title:
            raise MissingDataError("Couldn't extract title")
        if len(self.title) > Paper.max_length("title"):
            raise DataError(f"Title exceeds maximum length: {self.title}")
        if not self.paperhost_name:
            raise MissingDataError("Couldn't extract paperhost")
        if not self.abstract:
            raise MissingDataError("Couldn't extract abstract")
        if not self.published_at:
            raise MissingDataError("Couldn't extract date")


class DataUpdater(object):
    def __init__(self, log=print):
        self.log = log
        self.statistics = UpdateStatistics()

    @property
    def data_source(self):
        raise NotImplementedError

    def _get_all_articles(self):
        raise NotImplementedError

    def _get_article(self, doi):
        raise NotImplementedError

    def _count(self):
        raise NotImplementedError

    def get_or_create_db_article(self, datapoint, pdf_content, pdf_image, update_existing):
        try:
            db_article, created, updated = self.update_db(datapoint, update_existing=update_existing,
                                                          pdf_content=pdf_content, pdf_image=pdf_image)
            self.log(f"Updated/Created {datapoint.doi}")
            self.statistics.n_created += int(created)
            self.statistics.n_updated += int(updated)
            return db_article, created
        except MissingDataError as ex:
            id = datapoint.doi if datapoint.doi else f"\"{datapoint.title}\""
            self.log(f"Error: {id}: {ex.msg}")
            self.statistics.n_errors += 1
        except SkipArticle as ex:
            self.log(f"Skip: {datapoint.doi}: {ex.msg}")
            self.statistics.n_skipped += 1
        except NotCovidRelatedError as ex:
            self.log(f"Skip: {datapoint.doi}: {ex.msg}")
            self.statistics.n_skipped += 1
        except DifferentDataSourceError as ex:
            self.log(f"Skip: {datapoint.doi}: {ex.msg}")
            self.statistics.n_already_tracked += 1
        except ArticleModifiedError as ex:
            self.log(f"Conflict: {datapoint.doi}: {ex.msg}")
            self.statistics.n_conflicts += 1
        except (IntegrityError, DjangoDataError, PdfExtractError, DataError) as ex:
            self.log(f"Error: {datapoint.doi}: {ex}")
            self.statistics.n_errors += 1
        return None, None

    def get_new_data(self, pdf_content=True, pdf_image=True, progress=None):
        self.statistics = UpdateStatistics()
        self.statistics.start()

        total = self._count()
        self.log(f"Check {total} publications")

        iterator = progress(self._get_all_articles(), length=total) if progress else self._get_all_articles()

        for data_point in iterator:
            self.get_or_create_db_article(data_point, pdf_content=pdf_content, pdf_image=pdf_image,
                                          update_existing=False)

        self.log("Delete orphaned authors and journals")
        self.statistics.authors_deleted = Author.cleanup()
        self.statistics.journals_deleted = Journal.cleanup()

        self.statistics.stop()
        self.log(self.statistics)

    def update_existing_data(self, count=None, pdf_content=True, pdf_image=True, progress=None):
        self.statistics = UpdateStatistics()
        self.statistics.start()

        total = self._count()

        if count is None:
            count = total

        self.log(f"Update {count} existing articles")

        filtered_articles = Paper.objects.all().filter(data_source_value=self.data_source).order_by(
            F('last_scrape').asc(nulls_first=True))[:count]

        iterator = progress(filtered_articles) if progress else filtered_articles

        for article in iterator:
            data_point = self._get_article(doi=article.doi)
            if data_point:
                if data_point.update_timestamp and article.last_scrape > data_point.update_timestamp:
                    continue
                self.get_or_create_db_article(data_point, update_existing=True, pdf_content=pdf_content,
                                              pdf_image=pdf_image)

        self.log("Delete orphaned authors and journals")
        self.statistics.authors_deleted = Author.cleanup()
        self.statistics.journals_deleted = Journal.cleanup()

        self.statistics.stop()
        self.log(self.statistics)

    @staticmethod
    def update_pdf_data(db_article, extract_image=True, extract_content=True):
        """ Extract PDF data using the stored PDF url """
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

    def update_db(self, datapoint, update_existing, pdf_content, pdf_image):
        datapoint.check_integrity_constraints()

        with transaction.atomic():
            try:
                db_article = Paper.objects.get(doi=datapoint.doi)
                if DataSource.compare(db_article.data_source_value, self.data_source) > 0:
                    raise DifferentDataSourceError(
                        f"Article already tracked by {DataSource(db_article.data_source_value).name}")
                elif not update_existing and DataSource.compare(db_article.data_source_value, self.data_source) == 0:
                    raise SkipArticle("Article already in database")
                created = False
                # data_hash = data.get_hash()
                # if db_article.scrape_hash == data_hash:
                #     return db_article, created, False
                #
                # if db_article.modified:
                #     raise ArticleModifiedError(
                #         "Some fields are changed manually, but scrape recognized external updates"
                #     )
            except Paper.DoesNotExist:
                db_article = Paper(doi=datapoint.doi)
                created = True

            db_article.title = datapoint.title
            db_article.abstract = datapoint.abstract
            db_article.data_source_value = self.data_source
            db_article.published_at = datapoint.published_at

            db_article.covid_related = covid_related(db_article=db_article)
            if self.data_source.check_covid_related and not db_article.covid_related:
                raise NotCovidRelatedError("Article not covid related.")

            db_article.host, _ = PaperHost.objects.get_or_create(name=datapoint.paperhost_name)
            if datapoint.paperhost_url:
                db_article.host.url = datapoint.paperhost_url

            db_article.url = datapoint.url
            db_article.pdf_url = datapoint.pdf_url
            db_article.is_preprint = datapoint.is_preprint
            db_article.pubmed_id = datapoint.pubmed_id
            db_article.save()

            authors = datapoint.authors

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

            if datapoint.journal:
                db_article.journal, _ = Journal.objects.get_or_create(
                    name=datapoint.journal[:Journal.max_length("name")]
                )

            if pdf_content or pdf_image:
                self.update_pdf_data(db_article, extract_image=pdf_image, extract_content=pdf_content)
            db_article.version = datapoint.version

            db_article.last_scrape = timezone.now()

            db_article.categories.clear()
            db_article.save()
        return db_article, created, True
