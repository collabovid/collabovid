from django.shortcuts import render, HttpResponse, get_object_or_404, reverse
from django.http import HttpResponseNotFound
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from data.models import Paper, Category, Topic
import os
import requests
from search.search_engine import SearchEngine, get_default_search_engine

from django.conf import settings

PAPER_PAGE_COUNT = 10


def get_sorted_by_from_string(sorted_by):
    if sorted_by == "newest":
        return Paper.SORTED_BY_NEWEST
    elif sorted_by == "matching":
        return Paper.SORTED_BY_SCORE
    else:
        return Paper.SORTED_BY_TITLE


def home(request):
    if request.method == "GET":
        categories = Category.objects.order_by('name')

        return render(request, "core/home.html", {'papers': Paper.objects.all(), 'categories': categories})

def explore(request):
    if request.method == "GET":
        categories = Category.objects.order_by('name')
        topics = Topic.objects.all()

        return render(request, "core/explore.html",
                      {'categories': categories,
                       'topics': topics,
                       'search_url': reverse("explore")})

    elif request.method == "POST":
        category_names = request.POST.getlist("categories")
        search_query = request.POST.get("search", "")

        start_date = request.POST.get("published_at_start", "")
        end_date = request.POST.get("published_at_end", "")

        categories = Category.objects.filter(name__in=category_names)

        sorted_by = get_sorted_by_from_string(request.POST.get("sorted_by", ""))

        papers = Paper.get_paper_for_query(search_query,
                                           start_date,
                                           end_date,
                                           categories,
                                           Topic.objects.all(),
                                           sorted_by)

        if papers.count() > PAPER_PAGE_COUNT:
            paginator = Paginator(papers, PAPER_PAGE_COUNT)
            try:
                page_number = request.POST.get('page')
                page_obj = paginator.get_page(page_number)
            except PageNotAnInteger:
                page_obj = paginator.page(1)
            except EmptyPage:
                page_obj = None
        else:
            page_obj = papers

        return render(request, "core/partials/_search_results.html",
                      {'papers': page_obj, 'search_score_limit': 0, 'show_topic_score': False})

    return HttpResponseNotFound()


def about(request):
    return render(request, "core/about.html", {'papers': Paper.objects.all()})


def topic(request, id):
    topic = get_object_or_404(Topic, pk=id)

    if request.method == "GET":
        categories = set()
        for paper in topic.papers.all():
            categories.add(paper.category)

        papers = topic.papers.order_by('-topic_score')

        return render(request, "core/topic.html",
                      {'topic': topic,
                       'categories': categories,
                       'search_url': reverse("topic", args=(topic.pk,)),
                       'papers': papers})

    elif request.method == "POST":

        category_names = request.POST.getlist("categories")
        search_query = request.POST.get("search", "")

        start_date = request.POST.get("published_at_start", "")
        end_date = request.POST.get("published_at_end", "")

        categories = Category.objects.filter(name__in=category_names)

        sorted_by = get_sorted_by_from_string(request.POST.get("sorted_by", ""))

        papers = Paper.get_paper_for_query(search_query,
                                           start_date,
                                           end_date,
                                           categories,
                                           [topic],
                                           sorted_by)

        if papers.count() > PAPER_PAGE_COUNT:
            paginator = Paginator(papers, PAPER_PAGE_COUNT)
            try:
                page_number = request.POST.get('page')
                page_obj = paginator.get_page(page_number)
            except PageNotAnInteger:
                page_obj = paginator.page(1)
            except EmptyPage:
                page_obj = None
        else:
            page_obj = papers

        return render(request, "core/partials/_search_results.html",
                      {'papers': page_obj, 'search_score_limit': 0, 'show_topic_score': True})

    return HttpResponseNotFound()


def topic_overview(request):
    return render(request, "core/topic_overview.html", {'topics': Topic.objects.all()})


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


def search(request):
    if request.method == "GET":
        categories = Category.objects.order_by('name')

        return render(request, "core/search.html", {'papers': Paper.objects.all(),
                                                    'categories': categories,
                                                    'search_url': reverse("explore")})
    elif request.method == "POST":
        category_names = request.POST.getlist("categories")

        start_date = request.POST.get("published_at_start", "")
        end_date = request.POST.get("published_at_end", "")

        search_query = request.POST.get("search", "").strip()
        print(search_query)
        sorted_by = get_sorted_by_from_string(request.POST.get("sorted_by", ""))
        search_engine = get_default_search_engine()
        paginator = search_engine.search(search_query).paginator_ordered_by(sorted_by, page_count=PAPER_PAGE_COUNT)
        try:
            page_number = request.POST.get('page')
            page_obj = paginator.get_page(page_number)
        except PageNotAnInteger:
            page_obj = paginator.page(1)
        except EmptyPage:
            page_obj = None

        return render(request, "core/partials/_search_results.html", {'papers': page_obj,
                                                                      'search_score_limit': 0,
                                                                      'show_topic_score': False,})


