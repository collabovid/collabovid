from django.db.models import Q

from search.search import Search, PaperResult
from typing import List
from data.models import Paper

EXACT_SCORE = 1


class ExactSearch(Search):
    def find(self, query: str) -> List[PaperResult]:
        paper_dois = Paper.objects.filter(
            Q(title__icontains=query) | Q(abstract__icontains=query)).values_list('doi', flat=True)
        return [PaperResult(paper_doi=doi, score=EXACT_SCORE) for doi in paper_dois]
