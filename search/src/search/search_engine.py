from collections import defaultdict
from django.db.models import Q
from django.db.models import Value as V
from django.db.models.functions import Concat

from data.models import Paper, Author, Journal
from typing import List
from .search import Search
from .semantic_search import SemanticSearch
from .doi_search import DoiSearch
from .title_search import TitleSearch
from .author_search import AuthorSearch


class SearchEngine:
    def __init__(self, search_pipeline: List[Search]):
        self.search_pipeline = search_pipeline

    @staticmethod
    def filter_papers(start_date=None, end_date=None, topics=None, author_ids=None, author_and=False, journal_ids=None):
        papers = Paper.objects.all()

        filtered = False

        if journal_ids and len(journal_ids) > 0:
            journals = Journal.objects.filter(pk__in=journal_ids)
            papers = papers.filter(journal__in=journals)

        if author_ids and len(author_ids) > 0:
            authors = Author.objects.filter(pk__in=author_ids)

            if author_and:
                for author in authors:
                    papers = papers.filter(authors=author)
            else:
                papers = papers.filter(authors__in=authors)

            filtered = True

        if start_date:
            papers = papers.filter(published_at__gte=start_date)
            filtered = True

        if end_date:
            papers = papers.filter(published_at__lte=end_date)
            filtered = True

        if topics:
            papers = papers.filter(topic__in=topics)
            filtered = True

        return filtered, papers.distinct()

    def search(self, query: str, start_date=None, end_date=None, topics=None, author_ids=None, author_and=False,
               journal_ids=None, score_min=0.6):
        paper_score_table = defaultdict(int)

        filtered, papers = SearchEngine.filter_papers(start_date, end_date, topics, author_ids, author_and, journal_ids)

        combined_factor = 0

        paper_scores_items = dict()

        if not query:
            for doi in papers.values_list('doi', flat=True):
                paper_scores_items[doi] = 1
        else:
            for search_component in self.search_pipeline:
                paper_results, query = search_component.find(query, papers, score_min)

                print(search_component.__class__, query)

                found_sufficient_papers = False

                for result in paper_results:
                    if result.score > score_min:
                        paper_score_table[result.paper_doi] += result.score * search_component.weight
                        found_sufficient_papers = True

                if found_sufficient_papers:
                    # If a search component returns no papers its weight won't be taken into consideration
                    combined_factor += search_component.weight

                if not query or (found_sufficient_papers and search_component.exclusive):
                    #  In case an exclusive search found a result, we abort further search
                    #  In case query cleaning resulted in an empty query, we abort further search
                    print("breaking", query, found_sufficient_papers, search_component.exclusive)
                    break

            for doi, score in paper_score_table.items():
                paper_scores_items[doi] = score / combined_factor

        return paper_scores_items


def get_default_search_engine():
    """
    :return:
    """

    #  Note that the order is important as the search will be aborted if the doi search finds a matching paper.
    #  Moreover query cleaning will allow earlier search instances to clean the query for later ones.
    return SearchEngine([DoiSearch(), AuthorSearch(), TitleSearch(), SemanticSearch()])
