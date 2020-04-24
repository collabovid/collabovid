from django.db.models import Q

from search.search import Search, PaperResult
from typing import List
from data.models import Paper


class KeywordSearch(Search):
    def find(self, query: str) -> List[PaperResult]:
        pass
