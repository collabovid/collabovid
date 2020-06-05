from django.conf import settings
from django.utils.timezone import make_aware

from data.models import DataSource
from src.updater.data_updater import ArticleDataPoint, DataUpdater
from src.updater.elsevier_cache import ElsevierCache
from nameparser import HumanName
import datetime


class ElsevierDatapoint(ArticleDataPoint):
    def __init__(self, article_info):
        super().__init__()
        self.coredata = article_info['coredata']
        self.last_updated = make_aware(datetime.datetime.fromtimestamp(article_info['last_updated']))

    @property
    def doi(self):
        if 'prism:doi' in self.coredata and self.coredata['prism:doi']:
            return self.coredata['prism:doi'].strip()
        else:
            return None

    @property
    def title(self):
        if 'dc:title' in self.coredata and self.coredata['dc:title']:
            return self.coredata['dc:title']
        else:
            return None

    @property
    def abstract(self):
        if 'dc:description' in self.coredata and self.coredata['dc:description']:
            return self.coredata['dc:description']
        else:
            return None

    def extract_authors(self):
        authors = []
        if 'dc:creator' in self.coredata:
            for author in self.coredata['dc:creator']:
                if '$' in author:
                    human_name = HumanName(author['$'])
                    first_name = f'{human_name.first} {human_name.middle}'.strip()
                    last_name = human_name.last
                    authors.append((last_name, first_name))
        return authors

    @property
    def data_source(self):
        return DataSource.ELSEVIER

    @property
    def paperhost_name(self):
        return "Elsevier"

    @property
    def paperhost_url(self):
        return None

    @property
    def published_at(self):
        return datetime.datetime.strptime(self.coredata['prism:coverDate'], '%Y-%m-%d').date()

    @property
    def url(self):
        if 'link' in self.coredata and self.coredata['link']:
            for link in self.coredata['link']:
                if link['@rel'] == 'scidir':
                    return link['@href']
        return None

    @property
    def pdf_url(self):
        return None

    @property
    def version(self):
        return None

    @property
    def is_preprint(self):
        return False

    @property
    def category_name(self):
        return None

    @property
    def update_timestamp(self):
        return self.last_updated

    @property
    def journal(self):
        if 'prism:publicationName' in self.coredata and self.coredata['prism:publicationName']:
            return self.coredata['prism:publicationName']
        else:
            return None

    @staticmethod
    def _update_pdf_data(db_article, extract_image=True, extract_content=True):
        return


class ElsevierUpdater(DataUpdater):
    @property
    def data_source(self):
        return DataSource.ELSEVIER

    def __init__(self, log=print):
        super().__init__(log)
        self._metadata = None
        self._cache = ElsevierCache(path=f"{settings.RESOURCES_DIR}/cache/elsevier")
        self._cache.refresh()

    def _load_metadata(self):
        if not self._metadata:
            self._metadata = self._cache.get_metadata()

    def _count(self):
        self._load_metadata()
        return len(self._metadata)

    def _get_data_points(self):
        self._load_metadata()
        for doi, article_info in self._metadata.items():
            yield ElsevierDatapoint(article_info)

    def _get_data_point(self, doi):
        self._load_metadata()
        try:
            return ElsevierDatapoint(self._metadata[doi])
        except KeyError:
            return None
