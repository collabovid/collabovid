from datetime import date
from pymed import PubMed

from data.models import DataSource
from src.updater.data_updater import DataUpdater
from data.paper_db_insert import SerializableArticleRecord


class PubmedUpdater(DataUpdater):
    _PUBMED_SEARCH_QUERY = '("2019/12/01"[Date - Create] : "3000"[Date - Create]) AND ((COVID-19) OR (SARS-CoV-2) OR (Coronavirus)) AND Journal Article[ptyp]'

    @property
    def data_source(self):
        return DataSource.PUBMED

    def __init__(self, log=print, pdf_image=False, pdf_content=False, update_existing=False):
        super().__init__(log, pdf_image=pdf_image, pdf_content=pdf_content, update_existing=update_existing)
        self._query_result = None

    def _load_query_result(self):
        if not self._query_result:
            pubmed = PubMed(tool='Collabovid', email='info@collabovid.org')
            self._query_result = list(pubmed.query(query=self._PUBMED_SEARCH_QUERY, max_results=30000))

    def _count(self):
        self._load_query_result()
        return len(self._query_result)

    def _create_serializable_record(self, pubmed_article):
        """ Construct a serializable record from a given pubmed article (return value of pymed's query) """

        article = SerializableArticleRecord(doi=pubmed_article.doi, title=pubmed_article.title,
                                            abstract=pubmed_article.abstract, is_preprint=False)
        article.paperhost = "PubMed"
        article.datasource = DataSource.PUBMED
        publication_date = pubmed_article.publication_date
        if isinstance(publication_date, date):
            article.publication_date = pubmed_article.publication_date
        article.pubmed_id = pubmed_article.pubmed_id

        if article.pubmed_id:
            article.url = f"https://www.ncbi.nlm.nih.gov/pubmed/{article.pubmed_id}"

        try:
            article.journal = pubmed_article.journal
        except AttributeError:
            # Journal field is missing sometimes (e.g. pubmed ID 32479040). This is a book without DOI and won't get
            # added anyway.
            article.journal = None
        article.authors = [(a['lastname'], a['firstname']) for a in pubmed_article.authors
                           if a['lastname'] or a['firstname']]

        return article

    def _get_data_points(self):
        self._load_query_result()
        for pubmed_article in self._query_result:
            yield SerializableArticleRecord(pubmed_article)

    def _get_data_point(self, doi):
        self._load_query_result()
        try:
            return SerializableArticleRecord(next(x for x in self._query_result if x.doi == doi))
        except StopIteration:
            return None
