from django.db.models import Q

from search.search import Search, PaperResult
from typing import List
from data.models import Paper

TITLE_SCORE = 1
ABSTRACT_SCORE = 0.7


class ExactSearch(Search):
    def find(self, query: str) -> List[PaperResult]:
        title_matches = Paper.objects.filter(Q(title__icontains=query) | Q(abstract__icontains=query)).values_list(
            'doi', flat=True)
        abstract_matches = Paper.objects.filter(Q(abstract__icontains=query)).values_list('doi', flat=True)
        results = [PaperResult(paper_doi=doi, score=TITLE_SCORE) for doi in title_matches]
        results += [PaperResult(paper_doi=doi, score=ABSTRACT_SCORE) for doi in abstract_matches]
        return results
