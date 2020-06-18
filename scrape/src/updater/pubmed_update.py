from pymed import PubMed

from data.models import DataSource
from src.updater.data_updater import ArticleDataPoint, DataUpdater


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

    def _create_datapoint(self, pubmed_article):
        """ Construct a datapoint from a given pubmed article (return value of pymed's query) """

        article = ArticleDataPoint(doi=pubmed_article.doi, title=pubmed_article.title, abstract=pubmed_article.abstract,
                                   is_preprint=False)
        article.paperhost_name = "PubMed"
        article.datasource = DataSource.PUBMED
        article.published_at = pubmed_article.publication_date
        article.pubmed_id = pubmed_article.pubmed_id

        if article.pubmed_id:
            article.url = f"https://www.ncbi.nlm.nih.gov/pubmed/{article.pubmed_id}"

        try:
            article.jounal = pubmed_article.journal
        except AttributeError:
            # Journal field is missing sometimes (e.g. pubmed ID 32479040). This is a book without DOI and won't get
            # added anyway.
            article.journal = None
        article.authors = [(a['lastname'], a['firstname']) for a in pubmed_article.authors
                           if a['lastname'] or a['firstname']]

        return article

    def _get_all_articles(self):
        self._load_query_result()
        for pubmed_article in self._query_result:
            yield self._create_datapoint(pubmed_article)

    def _get_article(self, doi):
        self._load_query_result()
        try:
            return self._create_datapoint(next(x for x in self._query_result if x.doi == doi))
        except StopIteration:
            return None
