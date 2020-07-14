from django.shortcuts import render, get_object_or_404
from django.http import HttpResponseNotFound, JsonResponse, HttpResponse
from django.core.paginator import EmptyPage, PageNotAnInteger
from data.models import Paper, Category
from search.literature_utils.literature_file_analyzer import RisFileAnalyzer
from search.literature_utils.literature_file_exporter import RisFileExporter, BibTeXFileExporter

from search.suggestions_helper import SuggestionsHelper
from statistics import PaperStatistics

from search.request_helper import SearchRequestHelper, SimilarPaperRequestHelper

from search.forms import SearchForm, FindSimilarPapersForm
from search.tagify.tagify_searchable import *

from data.documents import AuthorDocument, JournalDocument, TopicDocument
from django.conf import settings
import io

MAX_UPLOAD_FILE_SIZE = 5000000  # in bytes, 5MB


def upload_ris(request):
    if request.method == "GET":
        return render(request, "search/similar_papers_upload.html")
    if request.method == "POST":

        form = FindSimilarPapersForm(request.POST, request.FILES)

        if form.is_valid():
            file_handle = request.FILES['file']

            print(file_handle.size)
            if file_handle.size < MAX_UPLOAD_FILE_SIZE:
                file_analyzer = RisFileAnalyzer(file_handle.read().decode('UTF-8'))

                return render(request, "search/ajax/_file_analysis.html", {
                    "file_analyzer": file_analyzer,
                })

        return HttpResponseNotFound()


def similar_papers(request):
    if request.method == "GET":
        dois = request.GET.getlist('dois')
        query_papers = Paper.objects.filter(pk__in=dois).all()

        return render(request, "search/search_similar_papers.html", {
            "query_papers": query_papers,
        })
    elif request.method == "POST":

        dois = request.POST.getlist('dois')
        query_papers = Paper.objects.filter(pk__in=dois).all()

        similar_request = SimilarPaperRequestHelper(list(query_papers.values_list('doi', flat=True)),
                                                    total_papers=30)

        return JsonResponse({
            'dois': similar_request.dois,
            'result_size': len(similar_request.dois)
        })


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


def export_search_result(request):
    if request.method == "GET":
        form = SearchForm(request.GET)

        if form.is_valid():
            search_response_helper = SearchRequestHelper(form)

            if not search_response_helper.error:
                search_result = search_response_helper.build_search_result()
                exporter = RisFileExporter(papers=search_result['paginator'].page(1))
                return exporter.build_response()

    return HttpResponseNotFound()


def export_paper(request, export_type, doi):
    if request.method == "GET":
        get_object_or_404(Paper, pk=doi)

        if export_type == 'ris':
            exporter = RisFileExporter(papers=Paper.objects.filter(pk=doi))
        elif export_type == 'bibtex':
            exporter = BibTeXFileExporter(papers=Paper.objects.filter(pk=doi))
        else:
            return HttpResponseNotFound()

        return exporter.build_response()

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
