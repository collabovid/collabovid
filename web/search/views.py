from django.shortcuts import render
from django.http import HttpResponseNotFound, JsonResponse
from django.core.paginator import EmptyPage, PageNotAnInteger
from data.models import GeoCity, GeoCountry, Paper, Author, Category, Journal, GeoLocation
from statistics import PaperStatistics

from search.request_helper import SearchRequestHelper

from django.contrib.postgres.search import TrigramSimilarity
from django.db.models import Value as V
from django.db.models.functions import Concat, Greatest
from django.db.models import Count, Max

import json

from search.forms import SearchForm
from search.tagify.tagify_searchable import *
PAPER_PAGE_COUNT = 10

def exploratory_search(request):
    if request.method == "GET":

        similar_paper_ids = request.GET.get('similarities', '')
        print(similar_paper_ids)

        try:
            similar_paper_ids = [str(pk) for pk in similar_paper_ids.split(',')] if similar_paper_ids else []
        except ValueError:
            similar_paper_ids = []

        print(similar_paper_ids)

        similar_papers = Paper.objects.filter(pk__in=similar_paper_ids)

        print(similar_papers)
        form = {
            "start_date": None,
            "end_date": None,
            "categories": Category.objects.all().order_by("pk"),
            'selected_categories': [],
            "tab": 'top',
            "authors": json.dumps([]),
            "authors-connection": 'all',
            "journals": json.dumps([]),
            "locations": json.dumps([]),
            "article_type": 'all'
        }

        return render(request, "core/similar_paper_search.html", {'form': form, 'similar_papers': similar_papers})

def explore(request):
    if request.method == "GET":
        return render(request, "core/explore.html")
    elif request.method == 'POST':
        return JsonResponse({'papers': [
            {
                'title': paper.title,
                'abstract': paper.abstract
            }
            for paper in Paper.objects.all()[:5]]})

    return HttpResponseNotFound()

def search(request):
    if request.method == "GET":

        form = SearchForm(request.GET)

        if form.is_valid():
            pass

        categories = Category.objects.all().order_by("pk")


        #authors = Author.objects.filter(pk__in=author_ids).annotate(name=Concat('first_name', V(' '), 'last_name'))

        #search_query = request.GET.get("search", "").strip()

        #form = {
        #    "start_date": start_date,
        #    "end_date": end_date,
        #    "search": search_query,
        #    "categories": categories,
        #    'selected_categories': selected_categories,
        #    "tab": tab,
        #    "authors": json.dumps(authors_to_json(authors)),
        #    "authors-connection": authors_connection,
        #    "journals": json.dumps(journals_to_json(journals)),
        #    "locations": json.dumps(locations_to_json(locations)),
        #    "article_type": article_type
        #}

        return render(request, "search/search.html", {'form': form})

    elif request.method == "POST":

        form = SearchForm(request.POST)

        if not form.is_valid():
            return render(request, "search/ajax/_search_result_error.html",
                          {'message': 'Your request is invalid.' + str(form.errors)})

        search_request = SearchRequestHelper(form)

        if search_request.error:
            return render(request, "search/ajax/_search_result_error.html",
                          {'message': 'We encountered an unexpected error. Please try again.'})

        if form.cleaned_data['tab'] == "statistics":
            statistics = PaperStatistics(search_request.papers)
            return render(request, "search/ajax/_statistics.html", {'statistics': statistics})
        else:
            if form.cleaned_data['tab']:
                sorted_by = Paper.SORTED_BY_SCORE
            else:
                sorted_by = Paper.SORTED_BY_NEWEST

            paginator = search_request.paginator_ordered_by(sorted_by, page_count=PAPER_PAGE_COUNT)
            try:
                page_number = request.POST.get('page')
                page_obj = paginator.get_page(page_number)
            except PageNotAnInteger:
                page_obj = paginator.page(1)
            except EmptyPage:
                page_obj = None

            return render(request, "search/ajax/_search_results.html", {'papers': page_obj,
                                                                          'show_score': False, })


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
