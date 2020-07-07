from django.conf import settings
from django.utils.timezone import make_aware

from data.models import DataSource
from src.pdf_extractor import PdfFromBytesExtractor
from src.updater.data_updater import DataUpdater
from src.updater.serializable_article_record import SerializableArticleRecord
from src.updater.elsevier_cache import ElsevierCache
from nameparser import HumanName
import datetime


class ElsevierUpdater(DataUpdater):
    @property
    def data_source(self):
        return DataSource.ELSEVIER

    def __init__(self, log=print, pdf_image=False, pdf_content=False, update_existing=False):
        super().__init__(log, pdf_image=pdf_image, pdf_content=pdf_content, update_existing=update_existing)
        self._metadata = None
        self._cache = ElsevierCache(path=f"{settings.RESOURCES_DIR}/cache/elsevier", log=log)
        self._cache.refresh()

    def _load_metadata(self):
        if not self._metadata:
            self._metadata = self._cache.get_metadata()

    def _count(self):
        self._load_metadata()
        return len(self._metadata)

    def _extract_authors(self, coredata):
        authors = []
        if 'dc:creator' in coredata:
            for author in coredata['dc:creator']:
                if '$' in author:
                    human_name = HumanName(author['$'])
                    first_name = f'{human_name.first} {human_name.middle}'.strip()
                    last_name = human_name.last
                    authors.append((last_name, first_name))
        return authors

    def _create_serializable_record(self, article_info):
        article = SerializableArticleRecord(is_preprint=False)
        coredata = article_info['coredata']

        if 'prism:doi' in coredata and coredata['prism:doi']:
            article.doi = coredata['prism:doi'].strip()
        if 'dc:title' in coredata and coredata['dc:title']:
            article.title = coredata['dc:title']
        if 'dc:description' in coredata and coredata['dc:description']:
            article.abstract = coredata['dc:description']
        article.datasource = DataSource.ELSEVIER
        article.paperhost = "Elsevier"

        article.publication_date = datetime.datetime.strptime(
                               article_info['originalText']['xocs:doc']['xocs:meta']['xocs:available-online-date']['$'],
                               '%Y-%m-%d').date()

        if 'link' in coredata and coredata['link']:
            for link in coredata['link']:
                if link['@rel'] == 'scidir':
                    article.url = link['@href']

        if 'prism:publicationName' in coredata and coredata['prism:publicationName']:
            article.journal = coredata['prism:publicationName']
        article.authors = self._extract_authors(coredata)
        article.update_timestamp = make_aware(datetime.datetime.fromtimestamp(article_info['last_updated']))

        return article

    def _get_data_points(self):
        self._load_metadata()
        for doi, article_info in self._metadata.items():
            yield self._create_serializable_record(article_info)

    def _get_data_point(self, doi):
        self._load_metadata()
        try:
            return self._create_serializable_record(self._metadata[doi])
        except KeyError:
            return None

    @staticmethod
    def update_pdf_data(db_article, extract_image=True, extract_content=True):
        if not extract_image and not extract_content:
            return
        with ElsevierCache(path=f"{settings.RESOURCES_DIR}/cache/elsevier") as elsevier:
            pdf = elsevier.get_pdf(db_article.doi)

        if extract_image and pdf:
            # The first page of all Elsevier PDFs is a Corona and license disclaimer
            image = PdfFromBytesExtractor.image_from_bytes(pdf, page=2)
            if image:
                db_article.add_preview_image(image)