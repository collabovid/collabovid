from django.db import transaction
from django.utils import timezone

from data.models import Author, DataSource, IgnoredPaper, Journal, Paper, PaperHost, ScrapeConflict
from src.static_functions import covid_related
from src.updater.serializable_article_record import SerializableArticleRecord


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

    def __init__(self, datasource, update_existing=False):
        self.datasource = datasource
        self.update_existing = update_existing

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
                    elif not self.update_existing and datasource_comparison == 0:
                        raise DatabaseUpdate.SkipArticle("Article already in database")

                    changed_externally = db_article.scrape_hash != datapoint.md5
                    changed_internally = db_article.manually_modified

                    if not changed_externally:
                        db_article.last_scrape = timezone.now()
                        db_article.save(set_manually_modified=False)
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
        elif len(datapoint.authors) == 0:
            error = "No authors"

        for author in datapoint.authors:
            if (
                    (author[1] and len(author[1]) > Author.max_length("first_name")) or
                    (author[0] and len(author[0]) > Author.max_length("last_name"))
            ):
                error = "Author name too long"
                error_msg = error + f": {author[0]}, {author[1]}"

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
        if datapoint.paperhost_url:
            db_article.host.url = datapoint.paperhost_url

        db_article.url = datapoint.url
        db_article.pdf_url = datapoint.pdf_url
        db_article.is_preprint = datapoint.is_preprint
        db_article.pubmed_id = datapoint.pubmed_id
        db_article.save(set_manually_modified=False)

        db_article.authors.clear()
        for author in datapoint.authors:
            db_author, _ = Author.get_or_create_by_name(
                first_name=author[1],
                last_name=author[0],
            )
            db_article.authors.add(db_author)

        if datapoint.journal:
            db_article.journal, _ = Journal.objects.get_or_create(
                name=datapoint.journal[:Journal.max_length("name")]
            )

        db_article.version = datapoint.version
        db_article.last_scrape = timezone.now()

        db_article.categories.clear()
        db_article.scrape_hash = datapoint.md5
        db_article.save(set_manually_modified=False)

    def _handle_conflict(self, db_article, datapoint):
        try:
            conflict = ScrapeConflict.objects.get(paper=db_article)
        except ScrapeConflict.DoesNotExist:
            conflict = ScrapeConflict(paper=db_article)
        conflict.datapoint = datapoint.json()
        conflict.save()