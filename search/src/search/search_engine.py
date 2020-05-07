from collections import defaultdict
from django.db.models import Q
from data.models import Paper
from typing import List
from .search import Search
from .exact_search import ExactSearch
from .keyword_search import KeywordSearch
from .semantic_search import SemanticSearch


class SearchEngine:
    def __init__(self, search_pipeline: List[Search]):
        self.search_pipeline = search_pipeline

    @staticmethod
    def filter_papers(categories, start_date=None, end_date=None, topics=None):
        papers = Paper.objects.filter(Q(category__in=categories))

        if start_date:
            papers = papers.filter(published_at__gte=start_date)

        if end_date:
            papers = papers.filter(published_at__lte=end_date)

        if topics:
            papers = papers.filter(topic__in=topics)
        return papers

    def search(self, query: str, categories: List, start_date=None, end_date=None, topics=None, score_min=0.6):
        paper_score_table = defaultdict(int)

        papers = SearchEngine.filter_papers(categories, start_date, end_date, topics)

        for search_component in self.search_pipeline:
            paper_results = search_component.find(query, papers)
            for result in paper_results:
                paper_score_table[result.paper_doi] += result.score

        paper_scores_items = dict()
        for doi, score in paper_score_table.items():
            if score >= score_min:
                paper_scores_items[doi] = score

        return paper_scores_items


def get_default_search_engine():
    return SearchEngine([ExactSearch(), KeywordSearch(), SemanticSearch()])
