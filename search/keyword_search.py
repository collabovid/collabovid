import os

import nltk
from django.db.models import Q

from search.search import Search, PaperResult
from typing import List
from data.models import Paper


KEYWORD_BASE_SCORE = 1


# Download nltk stopwords, if not exist
try:
    nltk.data.find('stopwords')
except LookupError:
    if 'NLTK_DATA' in os.environ:
        nltk_data_dir = os.environ['NLTK_DATA']
        nltk.download('stopwords', download_dir=nltk_data_dir)
    else:
        nltk.download('stopwords')
stopwords = set(nltk.corpus.stopwords.stopwords.words('english'))


class KeywordSearch(Search):
    def find(self, query: str) -> List[PaperResult]:
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
            sql_query &= (
                    Q(title__unaccent__icontains=word) |
                    Q(abstract__unaccent__icontains=word)
            )

        papers = Paper.objects.filter(sql_query)

        n_keywords = len(keywords)
        result = []
        for paper in papers:
            title_keywords = 0
            for word in keywords:
                if word in paper.title:
                    title_keywords += 1
            score = KEYWORD_BASE_SCORE + (title_keywords / n_keywords)
            result.append(PaperResult(paper_doi=paper.doi, score=score))

        return result