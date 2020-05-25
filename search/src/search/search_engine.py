from collections import defaultdict
from django.db.models import Q
from django.db.models import Value as V
from django.db.models.functions import Concat

from data.models import Paper, Author
from typing import List
from .search import Search
from .exact_search import ExactSearch
from .keyword_search import KeywordSearch
from .semantic_search import SemanticSearch
from .doi_search import DoiSearch


class SearchEngine:
    def __init__(self, search_pipeline: List[Search]):
        self.search_pipeline = search_pipeline

    @staticmethod
    def filter_papers(start_date=None, end_date=None, topics=None, author_names=None, author_and=False):
        papers = Paper.objects.all()

        if author_names and len(author_names) > 0:
            authors = Author.objects.all().annotate(name=Concat('first_name', V(' '), 'last_name'))
            authors = authors.filter(name__in=author_names)

            if author_and:
                for author in authors:
                    papers = papers.filter(authors=author)
            else:
                papers = papers.filter(authors__in=authors)

        if start_date:
            papers = papers.filter(published_at__gte=start_date)

        if end_date:
            papers = papers.filter(published_at__lte=end_date)

        if topics:
            papers = papers.filter(topic__in=topics)
        return papers.distinct()

    def search(self, query: str, start_date=None, end_date=None, topics=None, author_names=None, author_and=False,
               score_min=0.6):
        paper_score_table = defaultdict(int)

        papers = SearchEngine.filter_papers(start_date, end_date, topics, author_names, author_and)

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
    return SearchEngine([ExactSearch(), KeywordSearch(), DoiSearch()])
