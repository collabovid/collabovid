from typing import List

from src.analyze import get_semantic_paper_search


class SemanticSearch:

    @staticmethod
    def find(score_table: dict, query: str, ids: List[str], score_min=0.6, top=None):

        similar_papers = [(doi, score) for doi, score in get_semantic_paper_search().query(query) if score > score_min]

        if top:
            similar_papers = sorted(similar_papers, key=lambda x: x[1], reverse=True)[:top]

        ids_set = set(ids) if ids else None

        for doi, score in similar_papers:
            if ids_set is None or doi in ids_set:
                score_table[doi] += score

        return query