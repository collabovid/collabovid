from collections import defaultdict
from data.models import Paper
from typing import List
from search.search import Search, PaperResult
import logging
from django.core.paginator import Paginator
from search.exact_search import ExactSearch
from search.keyword_search import KeywordSearch


class ScoreSortPaginator(Paginator):
    def page(self, number):
        """Return a Page object for the given 1-based page number."""
        number = self.validate_number(number)
        bottom = (number - 1) * self.per_page
        top = bottom + self.per_page
        if top + self.orphans >= self.count:
            top = self.count
        paper_score_table = dict()
        for paper_doi, score in self.object_list[bottom:top]:
            paper_score_table[paper_doi] = score
        papers = Paper.objects.filter(pk__in=paper_score_table.keys())
        papers = sorted(papers, key=lambda paper: paper_score_table[paper.doi], reverse=True)
        return self._get_page(papers, number, self)


class SearchResult:
    def __init__(self, paper_score_table):
        self.paper_score_table = paper_score_table

    def paginator_ordered_by(self, criterion, page_count=10):
        if criterion == Paper.SORTED_BY_TITLE:
            paginator = Paginator(self.papers.order_by("title"), page_count)
        elif criterion == Paper.SORTED_BY_NEWEST:
            paginator = Paginator(self.papers.order_by("-published_at"), page_count)
        elif criterion == Paper.SORTED_BY_SCORE:
            paper_score_items = sorted(list(self.paper_score_table.items()), key=lambda x: x[1], reverse=True)
            paginator = ScoreSortPaginator(paper_score_items, page_count)
        else:
            paginator = Paginator(self.papers, page_count)
            logger = logging.getLogger(__name__)
            logger.warning("Unknown sorted by" + criterion)
        return paginator

    @property
    def papers(self):
        return Paper.objects.filter(pk__in=self.paper_score_table.keys())


class SearchEngine:
    def __init__(self, search_pipeline: List[Search]):
        self.search_pipeline = search_pipeline

    def search(self, query: str):
        paper_score_table = defaultdict(int)
        for search_component in self.search_pipeline:
            paper_results = search_component.find(query)
            for result in paper_results:
                paper_score_table[result.paper_doi] += result.score
        return SearchResult(paper_score_table)


def get_default_search_engine():
    return SearchEngine([ExactSearch(), KeywordSearch()])
