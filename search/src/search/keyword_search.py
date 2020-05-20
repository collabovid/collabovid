import os

import nltk
from django.db.models import Q, QuerySet

from .search import Search, PaperResult
from typing import List
from data.models import Paper


KEYWORD_BASE_SCORE = 0.8


# Download nltk stopwords, if not exist
try:
    nltk.data.find('stopwords')
except LookupError:
    if 'NLTK_DATA' in os.environ:
        nltk_data_dir = os.environ['NLTK_DATA']
        nltk.download('stopwords', download_dir=nltk_data_dir)
    else:
        nltk.download('stopwords')
stopwords = set(nltk.corpus.stopwords.words('english'))


class KeywordSearch(Search):
    def find(self, query: str, papers: QuerySet) -> List[PaperResult]:
        """
        Search for records, containing all keywords of query. Stopwords are excluded before. If all words in query are
        stopwords, use stopwords instead.

        :param query: Search query.
        :return: DOIs of papers, containing the keywords.
        """
        keywords = set(query.split()) - stopwords
        if len(keywords) == 0:
            # In case that query consists of stopwords only, use stopwords for search
            keywords = query.split()

        sql_query = Q()
        for word in keywords:
            # Each keyword must be contained in title OR in abstract
            sql_query &= (Q(title__icontains=word))

        paper_dois = papers.filter(sql_query).values_list('doi', flat=True)
        return [PaperResult(paper_doi=doi, score=KEYWORD_BASE_SCORE) for doi in paper_dois]