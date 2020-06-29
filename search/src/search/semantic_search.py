from typing import List

from .search import Search, PaperResult
from src.analyze import get_semantic_paper_search


class SemanticSearch(Search):
    def find(self, paper_score_table: dict, query: str, ids: List[str], score_min):

        score_dict = dict()
        for doi, score in get_semantic_paper_search().query(query):
            score_dict[doi] = score

        for doi in ids:
            if doi in score_dict and score_dict[doi] > score_min:
                paper_score_table[doi] += score_dict[doi]

        return query


    def compute_similars(self, page: dict, query: str, score_min):
        score_dict = dict()
        for doi, score in [(doi, score) for (doi, score) in get_semantic_paper_search().query(query) if doi in page]:
            score_dict[doi] = score

        for doi, infos in page.items():
            infos['similar'] = False
            if doi in score_dict:
                infos['similar'] = score_dict[doi] > score_min

