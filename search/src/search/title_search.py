from django.conf import settings
from django.db.models import Q, QuerySet

from .search import Search, PaperResult
from typing import List

from django.contrib.postgres.search import SearchQuery, SearchRank, SearchVector
from django.contrib.postgres.search import TrigramDistance

class TitleSearch(Search):

    def find(self, query: str, papers: QuerySet, score_min):
        """

        :param query:
        :param papers:
        :param score_min:
        :return:
        """

        if settings.USING_POSTGRES:

            vector = SearchVector('title', weight='A')
            search_query = SearchQuery(query, search_type="phrase")
            rank = SearchRank(vector, search_query)

            papers = papers.annotate(rank=rank).filter(rank__gte=score_min)

            return [PaperResult(paper_doi=paper.doi,
                                score=paper.rank)
                    for paper in papers], query

        else:
            title_matches = papers.filter(Q(title__icontains=query)).values_list(
                'doi', flat=True)
            return [PaperResult(paper_doi=doi, score=1) for doi in title_matches], query