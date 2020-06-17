from pymed import PubMed

from data.models import DataSource
from src.updater.data_updater import ArticleDataPoint, DataUpdater


class PubMedDatapoint(ArticleDataPoint):
    def __init__(self, raw_article):
        super().__init__()
        self.pubmed_article = raw_article

    @property
    def doi(self):
        return self.pubmed_article.doi

    @property
    def title(self):
        return self.pubmed_article.title

    @property
    def abstract(self):
        return self.pubmed_article.abstract

    def extract_authors(self):
        return [(a['lastname'], a['firstname']) for a in self.pubmed_article.authors if a['lastname'] or a['firstname']]

    @property
    def data_source(self):
        return DataSource.PUBMED

    @property
    def paperhost_name(self):
        return "PubMed"

    @property
    def pubmed_id(self):
        return self.pubmed_article.pubmed_id

    @property
    def paperhost_url(self):
        return None

    @property
    def published_at(self):
        return self.pubmed_article.publication_date

    @property
    def url(self):
        pmid = self.pubmed_id
        if pmid:
            return f"https://www.ncbi.nlm.nih.gov/pubmed/{pmid}"
        else:
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
    def journal(self):
        return self.pubmed_article.journal

    @staticmethod
    def update_pdf_data(db_article, extract_image=True, extract_content=True):
        return


class PubmedUpdater(DataUpdater):
    _PUBMED_SEARCH_QUERY = '("2019/12/01"[Date - Create] : "3000"[Date - Create]) AND ((COVID-19) OR (SARS-CoV-2) OR (Coronavirus)) AND Journal Article[ptyp]'

    @property
    def data_source(self):
        return DataSource.PUBMED

    def __init__(self, log=print):
        super().__init__(log)
        self._query_result = None

    def _load_query_result(self):
        if not self._query_result:
            pubmed = PubMed(tool='Collabovid', email='info@collabovid.org')
            self._query_result = list(pubmed.query(query=self._PUBMED_SEARCH_QUERY, max_results=30000))

    def _count(self):
        self._load_query_result()
        return len(self._query_result)

    def _get_data_points(self):
        self._load_query_result()
        for pubmed_article in self._query_result:
            yield PubMedDatapoint(pubmed_article)

    def _get_data_point(self, doi):
        self._load_query_result()
        try:
            return PubMedDatapoint(next(x for x in self._query_result if x.doi == doi))
        except StopIteration:
            return None
