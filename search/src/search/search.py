from typing import List, Tuple


class PaperResult:
    def __init__(self, paper_doi, score=None):
        self.paper_doi = paper_doi
        self.score = score


class Search:
    def __init__(self, *args, **kwargs):
        pass

    def find(self, paper_score_table: dict, query: str, ids: List[str], score_min) -> Tuple[List[PaperResult], str]:
        raise NotImplementedError()

    @property
    def weight(self):
        return 1

    @property
    def exclusive(self):
        return False

