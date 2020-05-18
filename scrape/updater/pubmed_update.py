from collections import OrderedDict
from datetime import datetime

import xmltodict

from data.models import DataSource
from scrape.updater.data_updater import ArticleDataPoint, DataError, DataUpdater


class PubMedDatapoint(ArticleDataPoint):
    def __init__(self, raw_article):
        super().__init__()
        self.raw_article = raw_article

    @property
    def doi(self):
        try:
            if type(self.raw_article['PubmedData']['ArticleIdList']['ArticleId']) is not list:
                id_fields = [self.raw_article['PubmedData']['ArticleIdList']['ArticleId']]
            else:
                id_fields = self.raw_article['PubmedData']['ArticleIdList']['ArticleId']
            doi = [x['#text'] for x in id_fields if x['@IdType'] == 'doi']

            if len(doi) == 1:
                return doi[0]
            return None
        except KeyError:
            return None

    @property
    def title(self):
        try:
            title = self.raw_article['MedlineCitation']['Article']['ArticleTitle']
            if type(title) is not str:
                raise DataError("Title contains HTML, wrong parsed in XML file")
            return self.raw_article['MedlineCitation']['Article']['ArticleTitle']
        except KeyError:
            return None

    @property
    def abstract(self):
        # TODO: approx. 3000/9000 wo abstract
        try:
            abs_text = self.raw_article['MedlineCitation']['Article']['Abstract']['AbstractText']
            if type(abs_text) is str:
                return abs_text
            elif type(abs_text) is list:
                return '\n'.join([x['#text'] for x in abs_text if '#text' in x])
            elif type(abs_text) is OrderedDict:
                # TODO: Get correct abstract. Same for title (Affects approx. 679/9000 records)
                raise DataError("Abstract contains HTML, wrong parsed in XML file")
            return None
        except KeyError:
            return None

    def extract_authors(self):
        authors = []
        try:
            raw_authors = self.raw_article['MedlineCitation']['Article']['AuthorList']['Author']
            if type(raw_authors) is not list:
                raw_authors = [raw_authors]
            for author in raw_authors:
                if type(author) is not OrderedDict:
                    continue
                if 'CollectiveName' in author and not ('LastName' in author and 'ForeName' in author):
                    continue
                authors.append((author['LastName'], author['ForeName']))
            return authors
        except KeyError:
            return []

    @property
    def data_source_name(self):
        return DataSource.PUBMED_DATASOURCE_NAME

    @property
    def paperhost_name(self):
        return "PubMed"  # TODO!

    @property
    def pubmed_id(self):
        try:
            if type(self.raw_article['PubmedData']['ArticleIdList']['ArticleId']) is not list:
                id_fields = [self.raw_article['PubmedData']['ArticleIdList']['ArticleId']]
            else:
                id_fields = self.raw_article['PubmedData']['ArticleIdList']['ArticleId']
            pmid = [x['#text'] for x in id_fields if x['@IdType'] == 'pubmed']

            if len(pmid) == 1:
                return pmid[0]
            return None
        except KeyError:
            return None

    @property
    def paperhost_url(self):
        return None

    @property
    def published_at(self):
        try:
            year = int(self.raw_article['MedlineCitation']['DateRevised']['Year'])
            month = int(self.raw_article['MedlineCitation']['DateRevised']['Month'])
            day = int(self.raw_article['MedlineCitation']['DateRevised']['Day'])
            return datetime(year, month, day).date()
        except KeyError:
            return None
        except ValueError:
            return None

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
    def category_name(self):
        return None

    @staticmethod
    def _update_pdf_data(db_article, extract_image=True, extract_content=True):
        return


class PubmedUpdater(DataUpdater):
    @property
    def data_source_name(self):
        return DataSource.MEDBIORXIV_DATASOURCE_NAME

    def __init__(self, log=print):
        super().__init__(log)
        self.metadata = None

    def _count(self):
        pass

    def _get_data_points(self):
        with open('resources/pubmed_result.xml', 'r') as file:
            self.metadata = xmltodict.parse(file.read())['PubmedArticleSet']['PubmedArticle']

        for raw_article in self.metadata:
            yield PubMedDatapoint(raw_article)

    def _get_data_point(self, doi):
        raise NotImplementedError
