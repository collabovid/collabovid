from django.conf import settings
from django.db.models import Q, QuerySet

from typing import List

from django.contrib.postgres.search import SearchQuery, SearchRank, SearchVector
from django.contrib.postgres.search import TrigramDistance

class TitleSearch:
    """
    This class replaces Elasticsearch when we want to develop other aspects of search.
    """

    @staticmethod
    def find(score_table: dict, query: str, papers: QuerySet, ):
        """
        :param score_table
        :param query:
        :param papers:
        :param score_min:
        :return:
        """

        if settings.USING_POSTGRES:

            vector = SearchVector('title', weight='A')
            search_query = SearchQuery(query, search_type="phrase")
            rank = SearchRank(vector, search_query)

            papers = papers.annotate(rank=rank).filter(rank__gte=0.6)

            for paper in papers:
                score_table[paper.doi] += paper.rank

        else:
            title_matches = papers.filter(Q(title__icontains=query)).values_list(
                'doi', flat=True)

            for paper in title_matches:
                score_table[paper.doi] += 1
