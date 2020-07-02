from django.shortcuts import render
from django.http import HttpResponseNotFound, JsonResponse
from django.core.paginator import EmptyPage, PageNotAnInteger
from data.models import Paper
from search.suggestions_helper import SuggestionsHelper
from statistics import PaperStatistics

from search.request_helper import SearchRequestHelper

from django.contrib.postgres.search import TrigramSimilarity
from django.db.models import Value as V, When, Case, IntegerField
from django.db.models.functions import Greatest

from search.forms import SearchForm
from search.tagify.tagify_searchable import *

from data.documents import AuthorDocument, JournalDocument

PAPER_PAGE_COUNT = 10


def search(request):
    if request.method == "GET":

        form = SearchForm(request.GET)
        if form.is_valid():
            pass

        return render(request, "search/search.html", {'form': form})
    elif request.method == "POST":
        form = SearchForm(request.POST)
        return render_search_result(request, form)

    return HttpResponseNotFound()


def render_search_result(request, form):
    if not form.is_valid():
        return render(request, "search/ajax/_search_result_error.html",
                      {'message': 'Your request is invalid.' + str(form.errors)})

    search_response_helper = SearchRequestHelper(form)

    if search_response_helper.error:
        return render(request, "search/ajax/_search_result_error.html",
                      {'message': 'We encountered an unexpected error. Please try again.'})

    if form.cleaned_data['tab'] == "statistics":
        #statistics = PaperStatistics(search_response_helper.papers)
        statistics = None
        return render(request, "search/ajax/_statistics.html", {'statistics': statistics})
    else:
        search_result = search_response_helper.build_search_result()
        try:
            page_obj = search_result['paginator'].page(search_result['paginator'].fixed_page)
        except (PageNotAnInteger, EmptyPage):
            page_obj = None

        search_result['papers'] = page_obj

        return render(request, "search/ajax/_search_results.html", search_result)


def list_authors(request):
    query = request.GET.get('query', '')

    if query:
        authors = SuggestionsHelper.compute_suggestions(model=Author,
                                                        search=AuthorDocument.search(),
                                                        query=query, field='full_name_suggest')
    else:
        authors = Author.objects.none()

    return JsonResponse({"authors": AuthorSearchable(authors=authors).dict})


def list_journals(request):
    query = request.GET.get('query', '')

    if query:
        journals = SuggestionsHelper.compute_suggestions(model=Journal,
                                                         search=JournalDocument.search(),
                                                         query=query, field='name_suggest').annotate(
            paper_count=Count('papers'))
    else:
        journals = Journal.objects.annotate(paper_count=Count('papers')).order_by('-paper_count')[:6]

    return JsonResponse({"journals": JournalSearchable(journals=journals).dict})


def list_locations(request):
    locations = GeoLocation.objects.all().annotate(paper_count=Count('papers'))

    query = request.GET.get('query', '')

    if query:
        locations = locations.annotate(similarity_name=TrigramSimilarity('name', query)).annotate(
            similarity_alias=TrigramSimilarity('alias', query)).annotate(
            similarity=Greatest('similarity_name', 'similarity_alias')).order_by('-similarity')[:6]
    else:
        locations = locations.order_by('-paper_count')[:6]

    return JsonResponse({"locations": LocationSearchable(locations=locations).dict})
