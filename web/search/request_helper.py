import requests
from django.conf import settings
import logging
from data.models import Paper
from django.core.paginator import Paginator

from search.forms import SearchForm
from search.paginator import FakePaginator


class SearchRequestHelper:

    def __init__(self, form: SearchForm, score_min=0.6):
        logger = logging.getLogger(__name__)

        self._response = None
        self._error = False

        try:
            response = requests.get(form.url, params={
                'form': form.to_json(),
                'score_min': score_min
            })
            response.raise_for_status()

            self._response = response.json()
        except requests.exceptions.Timeout:
            logger.error("Search Request Connection Timeout")
            self._error = True
        except requests.exceptions.HTTPError:
            self._error = True
            logger.error("Http Error occured")
        except requests.exceptions.RequestException:
            logger.error("Some unknown request exception occured")
            self._error = True

        if self._response is None:
            self._error = True

    @property
    def error(self):
        return self._error

    @property
    def response(self):
        return self._response

    def paginator(self):
        if not self.error:

            result_dois = [p['doi'] for p in self.response['results']]
            papers = sorted(list(Paper.objects.filter(pk__in=result_dois).all()), key=lambda x: result_dois.index(x.doi))

            for paper, infos in zip(papers, self.response['results']):
                if 'title' in infos:
                    paper.title = infos['title']
                if 'abstract' in infos:
                    paper.abstract = infos['abstract']
                if 'authors.full_name' in infos:
                    highlighted_full_names = infos['authors.full_name']

                    for highlighted_full_name in highlighted_full_names:
                        cleaned_full_name = highlighted_full_name.replace('<em>', '').replace('</em>', '')

                        for author in paper.highlighted_authors:
                            if author.full_name == cleaned_full_name:
                                author.display_name = highlighted_full_name

                paper.is_similar = infos['similar']

            paginator = FakePaginator(total_count=self.response['count'],
                                      page=self.response['page'],
                                      per_page=self.response['per_page'],
                                      papers=papers)

            return paginator


class SimilarPaperRequestHelper:

    def __init__(self, doi, number_papers):
        logger = logging.getLogger(__name__)

        self._response = None
        self._error = False
        self._papers = None
        self._number_papers = number_papers
        try:
            response = requests.get(settings.SEARCH_SERVICE_URL + '/similar', params={
                'doi': doi,
            })
            response.raise_for_status()
            self._response = response.json()
        except requests.exceptions.Timeout:
            logger.error("Similar Request Connection Timeout")
            self._error = True
        except requests.exceptions.HTTPError:
            self._error = True
        except requests.exceptions.RequestException as e:
            logger.error("Some unknown request exception occured", e)
            self._error = True

        if self._response is None:
            self._error = True

    @property
    def paginator(self):
        paper_score_items = [(result['doi'], result['score']) for result in self._response['similar']]
        paper_score_items = sorted(paper_score_items, key=lambda x: x[1], reverse=True)
        paginator = ScoreSortPaginator(paper_score_items, self._number_papers)
        return paginator

    @property
    def error(self):
        return self._error

    @property
    def papers(self):
        return self._papers
