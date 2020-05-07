import re
from typing import List

from data.models import Paper
from django.db.models import QuerySet

from .search import Search, PaperResult

DOI_SEARCH_SCORE = 10

# Matches any DOI related string (DOI pr DOI URL)
doi_regex = re.compile(r'((https?://(www.)?)?doi\.org/)?10\.\d+/\S+')

class DoiSearch(Search):
    def find(self, query: str, papers: QuerySet) -> List[PaperResult]:
        """
        Searches List of papers, whose DOI matches exactly input query (at most one). If input query is not a DOI,
        an empty list is returned.

        :param query: Search query.
        :return: List of papers with requested DOI or empty list.
        """
        if doi_regex.fullmatch(query):
            paper_dois = papers.filter(doi=query).values_list('doi', flat=True)
            return [PaperResult(paper_doi=doi, score=DOI_SEARCH_SCORE) for doi in paper_dois]
        else:
            return []
