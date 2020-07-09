from django.shortcuts import render
from django.http import HttpResponseNotFound, JsonResponse
from django.core.paginator import EmptyPage, PageNotAnInteger
from data.models import Paper, Category
from search.suggestions_helper import SuggestionsHelper
from statistics import PaperStatistics

from search.request_helper import SearchRequestHelper

from django.contrib.postgres.search import TrigramSimilarity
from django.db.models import Value as V, When, Case, IntegerField
from django.db.models.functions import Greatest

from search.forms import SearchForm
from search.tagify.tagify_searchable import *

from data.documents import AuthorDocument, JournalDocument, TopicDocument
from django.conf import settings

PAPER_PAGE_COUNT = 10


def search(request):
    if request.method == "GET":

        form = SearchForm(request.GET)
        if form.is_valid():
            pass

        return render(request, "search/search.html", {'form': form, 'categories': Category.objects.all()})
    elif request.method == "POST":
        form = SearchForm(request.POST)
        return render_search_result(request, form)

    return HttpResponseNotFound()


def render_search_result(request, form):
    if not form.is_valid():
        return render(request, "search/ajax/_search_result_error.html",
                      {'message': 'Your request is invalid.' + str(form.errors)})

    search_response_helper = SearchRequestHelper(form, save_request=not request.user.is_authenticated)

    if search_response_helper.error:
        return render(request, "search/ajax/_search_result_error.html",
                      {'message': 'We encountered an unexpected error. Please try again.'})

    search_result = search_response_helper.build_search_result()

    if search_result['result_type'] == SearchForm.RESULT_TYPE_STATISTICS:
        statistics = PaperStatistics(search_result['papers'])
        return render(request, "search/ajax/_statistics.html", {
            'statistics': statistics,
            'default_result_type': SearchForm.defaults['result_type']})

    elif search_result['result_type'] == SearchForm.RESULT_TYPE_PAPERS:

        try:
            page_obj = search_result['paginator'].page(search_result['paginator'].fixed_page)
        except (PageNotAnInteger, EmptyPage):
            page_obj = None

        search_result['papers'] = page_obj
        search_result['use_paging'] = True

        return render(request, "search/ajax/_search_results.html", search_result)

    return render(request, "search/ajax/_search_result_error.html",
                  {'message': 'Your request uses an invalid result type.'})


def list_topics(request):
    query = request.GET.get('query', '')

    if settings.USING_ELASTICSEARCH:
        topics = SuggestionsHelper.compute_elasticsearch_suggestions(model=Topic,
                                                                     search=TopicDocument.search(),
                                                                     query=query, fields=['topic_name_suggest',
                                                                                          'topic_keyword_suggest'])
    else:
        topics = SuggestionsHelper.compute_postgres_suggestions(model=Topic, query=query)

    return JsonResponse({"topics": TopicSearchable(topics=topics).dict})


def list_authors(request):
    query = request.GET.get('query', '')

    if settings.USING_ELASTICSEARCH:
        authors = SuggestionsHelper.compute_elasticsearch_suggestions(model=Author,
                                                                      search=AuthorDocument.search(),
                                                                      query=query, fields=['full_name_suggest'])
    else:
        authors = SuggestionsHelper.compute_postgres_suggestions(model=Author, query=query)

    return JsonResponse({"authors": AuthorSearchable(authors=authors).dict})


def list_journals(request):
    query = request.GET.get('query', '')

    if settings.USING_ELASTICSEARCH:
        journals = SuggestionsHelper.compute_elasticsearch_suggestions(model=Journal,
                                                                       search=JournalDocument.search(),
                                                                       query=query, fields=['name_suggest']).annotate(
            paper_count=Count('papers'))
    else:
        journals = SuggestionsHelper.compute_postgres_suggestions(model=Journal, query=query)

    return JsonResponse({"journals": JournalSearchable(journals=journals).dict})


def list_locations(request):
    query = request.GET.get('query', '')

    locations = SuggestionsHelper.compute_postgres_suggestions(model=GeoLocation, query=query)

    return JsonResponse({"locations": LocationSearchable(locations=locations).dict})
