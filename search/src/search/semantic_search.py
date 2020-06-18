from django.db.models import QuerySet

from .search import Search, PaperResult
from src.analyze import get_semantic_paper_search


class SemanticSearch(Search):
    def find(self, query: str, papers: QuerySet, score_min):
        paper_scores = {doi: score for doi, score in get_semantic_paper_search().query(query)}
        return [PaperResult(paper_doi=doi, score=paper_scores[doi])
                for doi in papers.values_list('doi', flat=True) if
                doi in paper_scores and paper_scores[doi] > score_min], query
