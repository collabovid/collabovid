from time import sleep

from data.models import Author, Journal, Paper, PaperData
from django.db.models import F
from django.utils import timezone
from src.pdf_extractor import PdfExtractError, PdfFromUrlExtractor
from data.paper_db_insert import DatabaseUpdate
from src.updater.update_statistics import UpdateStatistics


class DataUpdater(object):
    def __init__(self, log=print, pdf_content=False, pdf_image=False, update_existing=False):
        self.log = log
        self.update_existing = update_existing
        self.pdf_image = pdf_image
        self.pdf_content = pdf_content
        self.db_updater = DatabaseUpdate(self.data_source, update_existing)

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

    def get_or_create_db_article(self, datapoint):
        try:
            db_article, created, updated = self.db_updater.insert(datapoint)
            if updated:
                self._update_pdf_data(db_article)
                if created:
                    self.statistics.n_created += int(created)
                else:
                    self.statistics.n_updated += int(updated)
                self.log(f"{'Create' if created else 'Updated'} {datapoint.doi}")
            else:
                self.statistics.n_skipped += 1
            return db_article, created
        except (DatabaseUpdate.Error, PdfExtractError) as ex:
            id = datapoint.doi if datapoint.doi else f"\"{datapoint.title}\""
            if self.update_existing:
                DataUpdater.set_last_scrape(datapoint)
            self.log(f"Error: {id}: {ex.msg}")
            self.statistics.n_errors += 1
        except DatabaseUpdate.SkipArticle as ex:
            self.statistics.n_skipped += 1
        return None, None

    def get_new_data(self, progress=None):
        self.statistics = UpdateStatistics()
        self.statistics.start()

        total = self._count()
        self.log(f"Check {total} publications")

        iterator = progress(self._get_data_points(), length=total) if progress else self._get_data_points()

        for data_point in iterator:
            self.get_or_create_db_article(data_point)

        self.log("Delete orphaned authors and journals")
        self.statistics.authors_deleted = Author.cleanup()
        self.statistics.journals_deleted = Journal.cleanup()

        self.statistics.stop()
        self.log(self.statistics)

    def update_existing_data(self, count=None, progress=None):
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

        iterator = ArticleDatapointIterator(filtered_articles, count, self._get_data_point)

        for article, data_point in progress(iterator, length=count):
            if data_point.update_timestamp and article.last_scrape > data_point.update_timestamp:
                DataUpdater.set_last_scrape(data_point)
                continue
            self.get_or_create_db_article(data_point)

        self.log(f"Missing Data Points: {iterator.missing_dois}")
        self.statistics.n_missing_datapoints = len(iterator.missing_dois)
        self.log("Delete orphaned authors and journals")
        self.statistics.authors_deleted = Author.cleanup()
        self.statistics.journals_deleted = Journal.cleanup()

        self.statistics.stop()
        self.log(self.statistics)

    def _update_pdf_data(self, db_article):
        if not self.pdf_image and not self.pdf_content:
            return
        if not db_article.pdf_url:
            return

        sleep(3)
        pdf_extractor = PdfFromUrlExtractor(db_article.pdf_url)

        if self.pdf_image:
            image = pdf_extractor.extract_image()
            if image:
                db_article.add_preview_image(image)

        if self.pdf_content:
            content = pdf_extractor.extract_contents()
            if content:
                if db_article.data:
                    db_article.data.content = content
                else:
                    db_content = PaperData.objects.create(content=content)
                    db_article.data = db_content


class ArticleDatapointIterator:
    """
    Iterator that yields articles and the corresponding datapoint for a list of articles.
    The datapoint is obtained using the given get_data_point function.
    Count is the max. number of tuples to yield (only existing datapoints are counted).
    """
    def __init__(self, articles, count, get_data_point):
        self._articles = articles
        self._get_data_point = get_data_point
        self.missing_dois = []
        self._count = count

    def __iter__(self):
        for i, article in enumerate(self._articles):
            if i >= self._count + len(self.missing_dois):
                break
            datapoint = self._get_data_point(doi=article.doi)
            if datapoint:
                yield article, datapoint
            else:
                self.missing_dois.append(article.doi)
