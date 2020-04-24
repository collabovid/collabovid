from search.search import Search, PaperResult
from typing import List
import analyze


class SemanticSearch(Search):
    def find(self, query: str) -> List[PaperResult]:
        paper_scores_items = analyze.get_analyzer().related(query)
        return [PaperResult(paper_doi=doi, score=score) for doi, score in paper_scores_items]
