from typing import List

from src.analyze import get_semantic_paper_search
from math import floor


class SemanticSearch:

    @staticmethod
    def find(score_table: dict, query: str, ids: List[str], top=None):

        ids_set = set(ids) if ids else None

        similar_papers = sorted([(doi, score) for doi, score in get_semantic_paper_search().query(query) if
                                 ids_set is None or doi in ids_set], key=lambda x: x[1], reverse=True)

        if top:
            similar_papers = similar_papers[:top]

        #  In case of a filtered result, we want to show at least the best result (and some other) when they are not
        #  worse than .2
        max_score = similar_papers[0][1]
        score_min = min(0.55, floor(max_score * 10) / 10)

        if score_min >= 0.2:
            for doi, score in similar_papers:
                if score >= score_min:
                    score_table[doi] += score
                else:
                    # List is sorted, thus we can break
                    break

        return query
