import re

from django.db import transaction
from django.utils import timezone

from data.models import (
    Author,
    AuthorNameResolution,
    AuthorPaperMembership, DataSource,
    IgnoredPaper,
    Journal,
    Paper,
    PaperHost,
    ScrapeConflict,
)

import json
from dataclasses import dataclass, field
import hashlib
from datetime import date
from typing import List, Optional, Tuple

from django.core.serializers.json import DjangoJSONEncoder


def covid_related(db_article):
    if db_article.published_at and db_article.published_at < date(year=2019, month=12, day=1):
        return False

    covid19_keywords = r'(corona.?virus|(^|\s)corona(\s|$)|covid.?(20)?19|(^|\s)covid(\s|$)|sars.?cov.?2|2019.?ncov)'

    return (bool(re.search(covid19_keywords, db_article.title, re.IGNORECASE)) or
            bool(db_article.abstract and re.search(covid19_keywords, db_article.abstract, re.IGNORECASE)) or
            bool((db_article.data and re.search(covid19_keywords, db_article.data.content, re.IGNORECASE)))
            )


@dataclass
class SerializableArticleRecord:
    doi: Optional[str] = None
    title: Optional[str] = None
    abstract: Optional[str] = None
    authors: List[Tuple[str, str]] = field(default_factory=list)
    datasource: Optional[str] = None
    paperhost: Optional[str] = None
    pubmed_id: Optional[str] = None
    publication_date: Optional[date] = None
    url: Optional[str] = None
    pdf_url: Optional[str] = None
    version: Optional[str] = None
    is_preprint: Optional[bool] = None
    journal: Optional[str] = None
    update_timestamp: Optional[str] = None
    _md5: Optional[str] = None

    @property
    def md5(self):
        if not self._md5:
            m = hashlib.md5(self.json().encode('utf-8'))
            self._md5 = m.hexdigest()[:22]  # Maximum length of MD5 is 22 hex digits
        return self._md5

    def json(self):
        return json.dumps(self.__dict__, sort_keys=True, cls=DjangoJSONEncoder)


class DatabaseUpdate:
    class UpdateException(Exception):
        def __init__(self, msg):
            self.msg = msg

        def __repr__(self):
            return self.msg

    class Error(UpdateException):
        pass

    class SkipArticle(UpdateException):
        pass

    def __init__(self, datasource, update_existing=False, force_update=False):
        self.datasource = datasource
        self.update_existing = update_existing
        self.force_update = force_update

    def insert(self, datapoint: SerializableArticleRecord):
        self._validate_integrity_constraints(datapoint)

        if IgnoredPaper.objects.filter(doi=datapoint.doi).exists():
            raise DatabaseUpdate.SkipArticle("DOI is on ignore list")

        conflict = False
        try:
            with transaction.atomic():
                try:
                    db_article = Paper.objects.get(doi=datapoint.doi)
                    created = False
                except Paper.DoesNotExist:
                    db_article = Paper(doi=datapoint.doi)
                    created = True

                if not created:
                    datasource_comparison = DataSource.compare(db_article.data_source_value, datapoint.datasource)
                    if datasource_comparison > 0:
                        datasource_name = DataSource(db_article.data_source_value).name
                        raise DatabaseUpdate.SkipArticle(f"Article already tracked by {datasource_name}")
                    elif not self.force_update and not self.update_existing and datasource_comparison == 0:
                        raise DatabaseUpdate.SkipArticle("Article already in database")

                    changed_externally = db_article.scrape_hash != datapoint.md5
                    changed_internally = db_article.manually_modified

                    if not self.force_update and not changed_externally:
                        db_article.last_scrape = timezone.now()
                        db_article.save()
                        return db_article, False, False  # Article was neither created, nor updated

                    if changed_internally:
                        conflict = True
                        raise DatabaseUpdate.Error("Conflict: Manual modification and external change")

                self._update(db_article, datapoint)
        except DatabaseUpdate.Error as ex:
            if conflict:
                self._handle_conflict(db_article, datapoint)
            raise ex

        return db_article, created, True  # Article was updated

    @staticmethod
    def _validate_integrity_constraints(datapoint: SerializableArticleRecord):
        error = None
        error_msg = None
        if not datapoint.doi:
            error = "Missing DOI"
        elif not datapoint.title:
            error = "Missing title"
        elif len(datapoint.title) > Paper.max_length('title'):
            error = "Title too long"
            error_msg = error + f": {datapoint.title}"
        elif not datapoint.abstract:
            error = "Missing abstract"
        elif not datapoint.publication_date:
            error = "Missing publication date"

        if datapoint.doi and '\n' in datapoint.doi:
            error = "DOI has line breaks"

        author_count = 0
        for author in datapoint.authors:
            if (
                    (author[1] and len(author[1]) > Author.max_length("first_name")) or
                    (author[0] and len(author[0]) > Author.max_length("last_name"))
            ):
                error = "Author name too long"
                error_msg = error + f": {author[0]}, {author[1]}"
            if not AuthorNameResolution.objects.filter(
                    source_first_name=author[1], source_last_name=author[0], target_author=None).exists():
                # Count only authors that are not on the author ignore list
                author_count += 1

        if author_count == 0:
            error = "No authors"

        if error:
            if not error_msg:
                error_msg = error
            raise DatabaseUpdate.Error(error_msg)

    def _update(self, db_article: Paper, datapoint: SerializableArticleRecord):
        db_article.title = datapoint.title
        db_article.abstract = datapoint.abstract
        db_article.published_at = datapoint.publication_date

        db_article.url = datapoint.url
        db_article.pdf_url = datapoint.pdf_url
        db_article.is_preprint = datapoint.is_preprint
        db_article.pubmed_id = datapoint.pubmed_id
        db_article.data_source_value = self.datasource
        db_article.covid_related = covid_related(db_article=db_article)

        if self.datasource.check_covid_related and not db_article.covid_related:
            raise DatabaseUpdate.Error("Article not covid related.")

        db_article.host, _ = PaperHost.objects.get_or_create(name=datapoint.paperhost)

        db_article.visualized = False
        db_article.vectorized = False
        db_article.save()

        AuthorPaperMembership.objects.filter(paper=db_article).delete()
        rank = 0
        for author in datapoint.authors:
            db_author, _ = Author.get_or_create_by_name(first_name=author[1], last_name=author[0])
            if db_author is not None:
                AuthorPaperMembership.objects.create(paper=db_article, author=db_author, rank=rank)
                rank += 1

        if datapoint.journal:
            db_article.journal, _ = Journal.objects.get_or_create(
                name=datapoint.journal[:Journal.max_length("name")]
            )

        db_article.version = datapoint.version
        db_article.last_scrape = timezone.now()

        db_article.categories.clear()
        db_article.scrape_hash = datapoint.md5
        db_article.save()

    @staticmethod
    def _handle_conflict(db_article, datapoint):
        try:
            conflict = ScrapeConflict.objects.get(paper=db_article)
        except ScrapeConflict.DoesNotExist:
            conflict = ScrapeConflict(paper=db_article)
        conflict.datapoint = datapoint.json()
        conflict.save()
