from django.conf import settings
from django.db.models import Q, QuerySet

from .search import Search, PaperResult

from django.contrib.postgres.search import TrigramSimilarity

class ExactTitleSearch(Search):

    def find(self, query: str, papers: QuerySet, score_min):
        """

        :param query:
        :param papers:
        :param score_min:
        :return:
        """

        if settings.USING_POSTGRES:

            very_similar_papers = papers.annotate(rank=TrigramSimilarity('title', query)).filter(rank__gt=0.9)
            print(very_similar_papers.count())
            return [PaperResult(paper_doi=paper.doi,
                                score=paper.rank)
                    for paper in very_similar_papers], query

        else:
            title_matches = papers.filter(Q(title__icontains=query)).values_list(
                'doi', flat=True)
            return [PaperResult(paper_doi=doi, score=1) for doi in title_matches], query

    @property
    def weight(self):
        return 2.0
