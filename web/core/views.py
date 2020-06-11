from datetime import timedelta
from json import JSONDecodeError

from timeit import default_timer as timer

from django.db.models import Q, Sum, F, Subquery, OuterRef, IntegerField
from django.shortcuts import render, get_object_or_404, reverse
from django.http import HttpResponseNotFound, JsonResponse, HttpResponse
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from data.models import GeoCity, GeoCountry, Paper, Topic, Author, Category, Journal
from statistics import PaperStatistics, CategoryStatistics

from django.utils.timezone import datetime
import requests

from django.conf import settings
from search.request_helper import SearchRequestHelper

from django.contrib.postgres.search import TrigramSimilarity
from django.db.models import Value as V
from django.db.models.functions import Concat, Greatest
from django.db.models import Count, Max

import json

PAPER_PAGE_COUNT = 10


def home(request):
    if request.method == "GET":
        statistics = PaperStatistics(Paper.objects.all())

        latest_date = Paper.objects.filter(published_at__lte=datetime.now().date()).latest('published_at').published_at

        most_recent_papers = Paper.objects.filter(published_at=latest_date).order_by('-created_at')
        return render(request, "core/home.html", {'statistics': statistics,
                                                  'most_recent_papers': most_recent_papers,
                                                  'most_recent_paper_statistics': PaperStatistics(most_recent_papers),
                                                  'most_recent_paper_date': latest_date})


def about(request):
    paper_count = Paper.objects.count()
    return render(request, "core/about.html", {'paper_count': paper_count})


def imprint(request):
    if settings.IMPRINT_URL is None or len(settings.IMPRINT_URL) == 0:
        return HttpResponseNotFound()

    content = requests.get(settings.IMPRINT_URL).text

    return render(request, "core/imprint.html", {"content": content})


def privacy(request):
    if settings.DATA_PROTECTION_URL is None or len(settings.DATA_PROTECTION_URL) == 0:
        return HttpResponseNotFound()

    content = requests.get(settings.DATA_PROTECTION_URL).text
    return render(request, "core/data_protection.html", {"content": content})


def category_overview(request):
    category_statistics = [CategoryStatistics(category) for category in Category.objects.all()]

    return render(request, "core/categories_overview.html", {"category_statistics": category_statistics})


def search(request):
    if request.method == "GET":

        categories = Category.objects.all().order_by("pk")
        selected_categories = request.GET.get("categories", None)

        start_date = request.GET.get("published_at_start", "")
        end_date = request.GET.get("published_at_end", "")

        authors_connection = request.GET.get("authors-connection", "one")

        if authors_connection not in ["one", "all"]:
            authors_connection = "one"

        tab = request.GET.get("tab", "top")

        if tab not in ["newest", "top", "statistics"]:
            tab = "top"

        article_type = request.GET.get("article-type", "all")

        if article_type not in ["all", "reviewed", 'preprints']:
            article_type = "all"

        journal_ids = request.GET.get("journals", None)

        try:
            journal_ids = [int(pk) for pk in journal_ids.split(',')] if journal_ids else []
        except ValueError:
            journal_ids = []

        try:
            selected_categories = [int(pk) for pk in selected_categories.split(',')] if selected_categories else []
        except ValueError:
            selected_categories = []

        journals = Journal.objects.filter(pk__in=journal_ids).annotate(paper_count=Count('papers')).order_by(
            '-paper_count')

        author_ids = request.GET.get("authors", None)
        try:
            if author_ids:
                author_ids = [int(pk) for pk in author_ids.split(',')]
            else:
                author_ids = []
        except ValueError:
            author_ids = []

        authors = Author.objects.filter(pk__in=author_ids).annotate(name=Concat('first_name', V(' '), 'last_name'))

        search_query = request.GET.get("search", "").strip()

        form = {
            "start_date": start_date,
            "end_date": end_date,
            "search": search_query,
            "categories": categories,
            'selected_categories': selected_categories,
            "tab": tab,
            "authors": json.dumps(authors_to_json(authors)),
            "authors-connection": authors_connection,
            "journals": json.dumps(journals_to_json(journals)),
            "article_type": article_type
        }

        return render(request, "core/search.html", {'form': form})

    elif request.method == "POST":

        categories = request.POST.get("categories", None)

        try:
            categories = [int(pk) for pk in categories.split(',')] if categories else []
        except ValueError:
            categories = []

        if len(categories) == 0:
            categories = [category.pk for category in Category.objects.all()]

        start_date = request.POST.get("published_at_start", "")
        end_date = request.POST.get("published_at_end", "")

        tab = request.POST.get("tab", "")

        authors = request.POST.get("authors", "")
        authors_connection = request.POST.get("authors-connection", "one")

        if authors_connection not in ["one", "all"]:
            authors_connection = "one"

        journals = request.POST.get("journals")

        search_query = request.POST.get("search", "").strip()

        article_type = request.POST.get("article-type", "all")

        search_request = SearchRequestHelper(start_date, end_date,
                                             search_query, authors, authors_connection, journals,
                                             categories, article_type)

        if search_request.error:
            return render(request, "core/partials/_search_result_error.html",
                          {'message': 'We encountered an unexpected error. Please try again.'})

        if tab == "statistics":
            statistics = PaperStatistics(search_request.papers)
            return render(request, "core/partials/statistics/_statistics.html", {'statistics': statistics})
        else:
            if tab == "top":
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

            return render(request, "core/partials/_search_results.html", {'papers': page_obj,
                                                                          'show_score': False, })


def geo(request):

    # Using a subquery to find the directly associated paper count
    paper_counts_subquery = Subquery(GeoCountry.objects.filter(pk=OuterRef('pk')).
                                     annotate(count=Count('papers')).values('count'),
                                     output_field=IntegerField())

    # Counting indirectly associated papers. Afterwards we annotate the subquery result and sum up the values.
    countries = GeoCountry.objects.annotate(count_indirect=Count('cities__papers', distinct=True))\
        .annotate(count_direct=paper_counts_subquery)\
        .annotate(count=F('count_indirect') + F('count_direct')).values('alpha_2', 'count')

    countries = {country['alpha_2']: country['count'] for country in countries}

    cities = GeoCity.objects.annotate(count=Count('papers'))

    cities = [
        {
            'name': city.name,
            'lon': city.longitude,
            'lat': city.latitude,
            'count': city.count
        }
        for city in cities
    ]

    return render(
        request,
        "core/map.html",
        {
            "countries": json.dumps(countries),
            "cities": json.dumps(cities),
        }
    )


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


def journals_to_json(journals):
    return_json = []
    for journal in journals:
        return_json.append({
            "pk": journal.pk,
            "value": journal.displayname,
            "count": journal.paper_count
        })
    return return_json


def list_journals(request):
    journals = Journal.objects.all().annotate(paper_count=Count('papers'))

    query = request.GET.get('query', '')

    if query:
        journals = journals.annotate(similarity_name=TrigramSimilarity('name', query)).annotate(
            similarity_alias=TrigramSimilarity('alias', query)).annotate(
            similarity=Greatest('similarity_name', 'similarity_alias')).order_by('-similarity')[:6]
    else:
        journals = journals.order_by('-paper_count')[:6]

    return JsonResponse({"journals": journals_to_json(journals)})
