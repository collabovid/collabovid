from django.shortcuts import render
from django.http import HttpResponseNotFound, JsonResponse, HttpResponse
from django.core.paginator import EmptyPage, PageNotAnInteger
from data.models import Paper
from search.suggestions_helper import SuggestionsHelper
from statistics import PaperStatistics

from search.request_helper import SearchRequestHelper, SimilarPaperRequestHelper

import rispy

from search.forms import SearchForm, FindSimilarPapersForm
from search.tagify.tagify_searchable import *

from data.documents import AuthorDocument, JournalDocument
from django.conf import settings
import io
import heapq

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

                entries = rispy.loads(file_handle.read().decode('UTF-8'))

                file_papers = []

                for entry in entries:
                    if "doi" in entry:
                        file_papers.append({"doi": entry["doi"], "title": entry["primary_title"]})

                found_papers = Paper.objects.filter(pk__in=[entry['doi'] for entry in file_papers])

                found_paper_dois = set(found_papers.values_list('doi', flat=True))

                ignored_papers = []

                for paper in file_papers:
                    if paper['doi'] not in found_paper_dois:
                        ignored_papers.append(paper)

                return render(request, "search/ajax/_ris_file_analysis.html", {
                    "found_papers": found_papers,
                    "ignored_papers": ignored_papers
                })

        return HttpResponse("nas jsadasndoij oijsdoij")


def similar_papers(request):

    if request.method == "GET":

        dois = request.GET.getlist('dois')

        query_papers = Paper.objects.filter(pk__in=dois).all()

        similar_request = SimilarPaperRequestHelper(list(query_papers.values_list('doi', flat=True)),
                                                    total_papers=20,
                                                    papers_per_page=20)
        papers = []

        if not similar_request.error:
            papers = similar_request.paginator.page(1)
        return render(request, "search/search_similar_papers.html", {
            "query_papers": query_papers,
            "similar_papers": papers,
            "error": similar_request.error
        })




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


def export_search_result(request):
    if request.method == "GET":
        form = SearchForm(request.GET)

        if form.is_valid():
            search_response_helper = SearchRequestHelper(form)

            if not search_response_helper.error:
                search_result = search_response_helper.build_search_result()

                # Open StringIO to grab in-memory file contents
                file = io.StringIO()

                entries = []

                for paper in search_result['paginator'].page(search_result['paginator'].fixed_page):
                    entry = {
                        'primary_title': paper.title,
                        'first_authors': [", ".join([author.last_name, author.first_name]) for author in paper.authors.all()],
                        'abstract': paper.abstract,
                        'doi': paper.doi,
                        'publication_year': paper.published_at.year,
                        'publisher': paper.host.name
                    }

                    if paper.pdf_url:
                        entry['url'] = paper.pdf_url

                    if paper.journal:
                        entry['journal_name'] = paper.journal.displayname
                        entry['type_of_reference'] = 'JOUR'
                    else:
                        entry['type_of_reference'] = 'GEN'

                    entries.append(entry)

                rispy.dump(entries, file)

                response = HttpResponse(file.getvalue(), content_type='application/x-research-info-systems')
                response['Content-Disposition'] = 'attachment; filename=collabovid-export.ris'

                return response

        return HttpResponseNotFound()


def render_search_result(request, form):
    if not form.is_valid():
        return render(request, "search/ajax/_search_result_error.html",
                      {'message': 'Your request is invalid.' + str(form.errors)})

    search_response_helper = SearchRequestHelper(form)

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

        return render(request, "search/ajax/_search_results.html", search_result)

    return render(request, "search/ajax/_search_result_error.html",
                  {'message': 'Your request uses an invalid result type.'})


def list_authors(request):
    query = request.GET.get('query', '')

    if settings.USING_ELASTICSEARCH:
        authors = SuggestionsHelper.compute_elasticsearch_suggestions(model=Author,
                                                                      search=AuthorDocument.search(),
                                                                      query=query, field='full_name_suggest')
    else:
        authors = SuggestionsHelper.compute_postgres_suggestions(model=Author, query=query)

    return JsonResponse({"authors": AuthorSearchable(authors=authors).dict})


def list_journals(request):
    query = request.GET.get('query', '')

    if settings.USING_ELASTICSEARCH:
        journals = SuggestionsHelper.compute_elasticsearch_suggestions(model=Journal,
                                                                       search=JournalDocument.search(),
                                                                       query=query, field='name_suggest').annotate(
            paper_count=Count('papers'))
    else:
        journals = SuggestionsHelper.compute_postgres_suggestions(model=Journal, query=query)

    return JsonResponse({"journals": JournalSearchable(journals=journals).dict})


def list_locations(request):
    query = request.GET.get('query', '')

    locations = SuggestionsHelper.compute_postgres_suggestions(model=GeoLocation, query=query)

    return JsonResponse({"locations": LocationSearchable(locations=locations).dict})
