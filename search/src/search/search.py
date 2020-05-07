from typing import List
from django.db.models import QuerySet


class PaperResult:
    def __init__(self, paper_doi, score=None):
        self.paper_doi = paper_doi
        self.score = score


class Search:
    def __init__(self, *args, **kwargs):
        pass

    def find(self, query: str, papers: QuerySet) -> List[PaperResult]:
        raise NotImplementedError()

