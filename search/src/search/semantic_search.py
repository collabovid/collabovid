from typing import List

from .search import Search, PaperResult
from src.analyze import get_semantic_paper_search


class SemanticSearch(Search):
    def find(self, paper_score_table: dict, query: str, ids: List[str], score_min):
        for doi, score in get_semantic_paper_search().query(query):
            if score > score_min:
                paper_score_table[doi] += score
        return query
