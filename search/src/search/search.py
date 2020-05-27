from typing import List, Tuple
from django.db.models import QuerySet


class PaperResult:
    def __init__(self, paper_doi, score=None):
        self.paper_doi = paper_doi
        self.score = score


class Search:
    def __init__(self, *args, **kwargs):
        pass

    def find(self, query: str, papers: QuerySet, score_min) -> Tuple[List[PaperResult], str]:
        raise NotImplementedError()

    @property
    def weight(self):
        return 1

    @property
    def exclusive(self):
        return False

