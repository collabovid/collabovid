import requests
from django.conf import settings
import logging
from data.models import Paper
from django.core.paginator import Paginator
from search.paginator import ScoreSortPaginator


class SearchRequestHelper:

    def __init__(self, categories, start_date, end_date, search_query):
        logger = logging.getLogger(__name__)

        self._response = None

        try:
            response = requests.get(settings.SEARCH_SERVICE_URL, params={
                'categories': categories,
                'start_date': start_date,
                'end_date': end_date,
                'search': search_query
            })
            response.raise_for_status()

            self._response = response.json()

        except requests.exceptions.Timeout:
            logger.error("Search Request Connection Timeout")
        except requests.exceptions.RequestException as e:
            logger.error("Some unknown request exception occured", e)
            raise

        self._papers = Paper.objects.filter(pk__in=self._response.keys())

    @property
    def papers(self):
        return self._papers

    def paginator_ordered_by(self, criterion, page_count=10):


        if criterion == Paper.SORTED_BY_TOPIC_SCORE:
            paginator = Paginator(self.papers.order_by("-topic_score"), page_count)
        elif criterion == Paper.SORTED_BY_NEWEST:
            paginator = Paginator(self.papers.order_by("-published_at"), page_count)
        elif criterion == Paper.SORTED_BY_SCORE:
            filtered_items = []
            for doi, score in self._response.items():
                filtered_items.append((doi, score))
            paper_score_items = sorted(filtered_items, key=lambda x: x[1], reverse=True)
            paginator = ScoreSortPaginator(paper_score_items, page_count)
        else:
            paginator = Paginator(self.papers, page_count)
            logger = logging.getLogger(__name__)
            logger.warning("Unknown sorted by" + criterion)
        return paginator
