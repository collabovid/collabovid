from django.shortcuts import render, get_object_or_404, reverse
from django.http import HttpResponseNotFound
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from data.models import Paper, Category, Topic
import requests
from search.search_engine import get_default_search_engine

from django.conf import settings
from analyze.statistics import Statistics

PAPER_PAGE_COUNT = 10


def home(request):
    if request.method == "GET":
        categories = Category.objects.order_by('name')

        return render(request, "core/home.html", {'papers': Paper.objects.all(), 'categories': categories})


def about(request):
    return render(request, "core/about.html", {'papers': Paper.objects.all()})


def topic(request, id):
    # TODO: Adapt search
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
        def get_sorted_by_from_string(sorted_by):
            if sorted_by == "newest":
                return Paper.SORTED_BY_NEWEST
            elif sorted_by == "matching":
                return Paper.SORTED_BY_SCORE
            else:
                return Paper.SORTED_BY_TITLE

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

        category_names = request.GET.getlist("categories")

        start_date = request.GET.get("published_at_start", "")
        end_date = request.GET.get("published_at_end", "")
        tab = request.GET.get("tab", "top")

        if tab not in ["newest", "top", "statistics"]:
            tab = "top"

        search = request.GET.get("search", "").strip()

        categories = Category.objects.order_by('name')

        if "all" in category_names or len(category_names) == 0:
            category_names = [category.name for category in categories]

        form = {
            "categories": category_names,
            "start_date": start_date,
            "end_date": end_date,
            "search": search,
            "tab": tab
        }

        return render(request, "core/search.html", {'form': form,
                                                    'papers': Paper.objects.all(),
                                                    'categories': categories})
    elif request.method == "POST":
        category_names = request.POST.getlist("categories")

        start_date = request.POST.get("published_at_start", "")
        end_date = request.POST.get("published_at_end", "")

        tab = request.POST.get("tab", "")

        search_query = request.POST.get("search", "").strip()
        search_engine = get_default_search_engine()

        search_result = search_engine.search(search_query, categories=category_names, start_date=start_date,
                                             end_date=end_date)

        if tab == "statistics":
            statistics = Statistics(search_result.papers)
            return render(request, "core/partials/statistics/_statistics.html", {'statistics': statistics})
        else:
            if tab == "top":
                sorted_by = Paper.SORTED_BY_SCORE
            else:
                sorted_by = Paper.SORTED_BY_NEWEST

            paginator = search_result.paginator_ordered_by(sorted_by, page_count=PAPER_PAGE_COUNT)
            try:
                page_number = request.POST.get('page')
                page_obj = paginator.get_page(page_number)
            except PageNotAnInteger:
                page_obj = paginator.page(1)
            except EmptyPage:
                page_obj = None

            return render(request, "core/partials/_search_results.html", {'papers': page_obj,
                                                                          'search_score_limit': 0,
                                                                          'show_topic_score': False, })
