from django.shortcuts import render, reverse
from django.http import HttpResponseNotFound, JsonResponse
from django.core.paginator import EmptyPage, PageNotAnInteger
from data.models import GeoCity, GeoCountry, Paper, Author, Category, Journal, GeoLocation
from statistics import PaperStatistics

from search.request_helper import SearchRequestHelper

from django.contrib.postgres.search import TrigramSimilarity
from django.db.models import Value as V
from django.db.models.functions import Greatest

from search.forms import SearchForm, SimilarSearchForm
from search.tagify.tagify_searchable import *

PAPER_PAGE_COUNT = 10


def exploratory_search(request):
    if request.method == "GET":
        form = SimilarSearchForm(request.GET)

        if form.is_valid():
            similar_papers = Paper.objects.filter(pk__in=form.cleaned_data['similar_papers'])
            different_papers = Paper.objects.filter(pk__in=form.cleaned_data['different_papers'])

            return render(request, "search/similar_paper_search.html", {'form': form,
                                                                        'search_url': reverse('exploratory-search'),
                                                                        'similar_papers': similar_papers,
                                                                        'different_papers': different_papers})
    elif request.method == "POST":
        form = SimilarSearchForm(request.POST)
        return render_search_result(request, form)


def explore(request):
    if request.method == "GET":
        return render(request, "search/explore.html")
    elif request.method == 'POST':

        form = SearchForm(request.POST)

        if form.is_valid():
            search_response_helper = SearchRequestHelper(form, score_min=0.1)
            papers = search_response_helper.paginator_ordered_by(Paper.SORTED_BY_SCORE, page_count=PAPER_PAGE_COUNT).page(
                1)[:5]

            print(len(papers))

            return JsonResponse({'papers': [
                {
                    'pk': paper.pk,
                    'title': paper.title,
                    'abstract': paper.abstract
                }
             for paper in papers]})

    return HttpResponseNotFound()


def search(request):
    if request.method == "GET":

        form = SearchForm(request.GET)
        if form.is_valid():
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
        statistics = PaperStatistics(search_response_helper.papers)
        return render(request, "search/ajax/_statistics.html", {'statistics': statistics})
    else:
        if form.cleaned_data['tab']:
            sorted_by = Paper.SORTED_BY_SCORE
        else:
            sorted_by = Paper.SORTED_BY_NEWEST

        paginator = search_response_helper.paginator_ordered_by(sorted_by, page_count=PAPER_PAGE_COUNT)
        try:
            page_number = request.POST.get('page')
            page_obj = paginator.get_page(page_number)
        except PageNotAnInteger:
            page_obj = paginator.page(1)
        except EmptyPage:
            page_obj = None

        return render(request, "search/ajax/_search_results.html", {'papers': page_obj})


def authors_to_json(authors):
    return_json = []

    for author in authors:
        return_json.append({
            "value": author.name,
            "pk": author.pk
        })
    return return_json


def list_authors(request):
    query = request.GET.get('query', '')

    if query:
        possible_authors = Author.objects.all().annotate(name=Concat('first_name', V(' '), 'last_name'))
        authors = possible_authors.annotate(similarity=TrigramSimilarity('name', query)).order_by(
            '-similarity')[:6]
    else:
        authors = []

    return JsonResponse({"authors": authors_to_json(authors)})


def list_journals(request):
    journals = Journal.objects.all().annotate(paper_count=Count('papers'))

    query = request.GET.get('query', '')

    if query:
        journals = journals.annotate(similarity_name=TrigramSimilarity('name', query)).annotate(
            similarity_alias=TrigramSimilarity('alias', query)).annotate(
            similarity=Greatest('similarity_name', 'similarity_alias')).order_by('-similarity')[:6]
    else:
        journals = journals.order_by('-paper_count')[:6]

    return JsonResponse({"journals": JournalSearchable(journals=journals).dict})


def locations_to_json(locations):
    return [
        {
            "pk": location.pk,
            "value": location.displayname,
            "count": location.paper_count
        }
        for location in locations.all()
    ]


def list_locations(request):
    locations = GeoLocation.objects.all().annotate(paper_count=Count('papers'))

    query = request.GET.get('query', '')

    if query:
        locations = locations.annotate(similarity_name=TrigramSimilarity('name', query)).annotate(
            similarity_alias=TrigramSimilarity('alias', query)).annotate(
            similarity=Greatest('similarity_name', 'similarity_alias')).order_by('-similarity')[:6]
    else:
        locations = locations.order_by('-paper_count')[:6]

    return JsonResponse({"locations": locations_to_json(locations)})
