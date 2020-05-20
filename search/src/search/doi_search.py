import re
from typing import List
from django.db.models import QuerySet
from .search import Search, PaperResult

DOI_SEARCH_SCORE = 10

# Matches any DOI related string (DOI pr DOI URL)
doi_regex = re.compile(r'((https?://(www.)?)?doi\.org/)?10\.\d+/\S+')

# Matches an arXiv ID string, either with or without the 'arxiv:' prefix
arxiv_regex = re.compile(r'(?P<prefix>ar[xX]iv:)?(?P<numeric_id>\d{4}.\d{4,5}|[a-z\-]+(\.[A-Z]{2})?/\d{7})(v\d+)?')


class DoiSearch(Search):
    def find(self, query: str, papers: QuerySet) -> List[PaperResult]:
        """
        Searches List of papers, whose DOI matches exactly input query (at most one). If input query is not a DOI
        or an arXiv ID, an empty list is returned.

        :param query: Search query.
        :return: List of papers with requested DOI/arXiv ID or empty list.
        """
        if doi_regex.fullmatch(query):
            paper_dois = papers.filter(doi=query).values_list('doi', flat=True)
            return [PaperResult(paper_doi=doi, score=DOI_SEARCH_SCORE) for doi in paper_dois]
        elif arxiv_regex.fullmatch(query):
            match = arxiv_regex.match(query)
            # make sure that the prefix 'arXiv:' (case sensitive!) is there, because we save it like this in the DB
            arxiv_id = 'arXiv:' + match.group('numeric_id')
            paper_dois = papers.filter(doi=arxiv_id).values_list('doi', flat=True)
            return [PaperResult(paper_doi=doi, score=DOI_SEARCH_SCORE) for doi in paper_dois]
        else:
            return []
