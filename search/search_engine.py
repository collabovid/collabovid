from collections import defaultdict
from django.db.models import Q
from data.models import Paper
from typing import List
from search.search import Search, PaperResult
import logging
from django.core.paginator import Paginator
from search.exact_search import ExactSearch
from search.keyword_search import KeywordSearch
from search.semantic_search import SemanticSearch


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
    def __init__(self, paper_score_items, categories, start_date=None, end_date=None):
        self.paper_score_items = paper_score_items
        self.categories = categories
        self.start_date = start_date
        self.end_date = end_date
        self.paper_dois = [doi for doi, _ in self.paper_score_items]

    def paginator_ordered_by(self, criterion, page_count=10):
        if criterion == Paper.SORTED_BY_TITLE:
            paginator = Paginator(self.papers.order_by("title"), page_count)
        elif criterion == Paper.SORTED_BY_NEWEST:
            paginator = Paginator(self.papers.order_by("-published_at"), page_count)
        elif criterion == Paper.SORTED_BY_SCORE:
            filtered_items = []
            dois = self.papers.values_list('doi', flat=True)
            for doi, score in self.paper_score_items:
                if doi in dois:
                    filtered_items.append((doi, score))
            paper_score_items = sorted(filtered_items, key=lambda x: x[1], reverse=True)
            paginator = ScoreSortPaginator(paper_score_items, page_count)
        else:
            paginator = Paginator(self.papers, page_count)
            logger = logging.getLogger(__name__)
            logger.warning("Unknown sorted by" + criterion)
        return paginator

    @property
    def papers(self):
        papers = Paper.objects.filter(Q(category__in=self.categories) & Q(pk__in=self.paper_dois))
        if self.start_date:
            papers = papers.filter(published_at__gte=self.start_date)

        if self.end_date:
            papers = papers.filter(published_at__lte=self.end_date)
        return papers


class SearchEngine:
    def __init__(self, search_pipeline: List[Search]):
        self.search_pipeline = search_pipeline

    def search(self, query: str, categories: List, start_date=None, end_date=None, score_min=0.6):
        paper_score_table = defaultdict(int)
        for search_component in self.search_pipeline:
            paper_results = search_component.find(query)
            for result in paper_results:
                paper_score_table[result.paper_doi] += result.score

        paper_scores_items = []
        for doi, score in paper_score_table.items():
            if score >= score_min:
                paper_scores_items.append((doi, score))
        return SearchResult(paper_scores_items, categories, start_date, end_date)


def get_default_search_engine():
    return SearchEngine([ExactSearch(), KeywordSearch(), SemanticSearch()])
