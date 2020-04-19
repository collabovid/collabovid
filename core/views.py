from django.shortcuts import render, HttpResponse, get_object_or_404, reverse
from django.http import HttpResponseNotFound
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from data.models import Paper, Category, Topic
import os

if 'USE_PAPER_ANALYZER' in os.environ and os.environ['USE_PAPER_ANALYZER'] == '1':
    import analyze

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
        return render(request, "core/home.html", {'papers': Paper.objects.all()})
    elif request.method == "POST":

        search_query = request.POST.get("query", "")

        papers = list()
        scores = list()

        page_obj = papers

        search_score_limit = 60

        if 'USE_PAPER_ANALYZER' in os.environ and os.environ['USE_PAPER_ANALYZER'] == '1':
            analyzer = analyze.get_analyzer()
            papers = analyzer.related(search_query).filter(search_score__gt=search_score_limit)

            sorted_by = get_sorted_by_from_string(request.POST.get("sorted_by", ""))
            papers = Paper.sort_papers(papers, sorted_by, score_field="search_score")

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

        return render(request, "core/partials/_custom_topic_search_result.html",
                      {'papers': page_obj, 'search_score_limit': search_score_limit/2})


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

        return render(request, "core/partials/_search_results.html", {'papers': page_obj, 'search_score_limit': 0, 'show_topic_score': False})

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

        return render(request, "core/partials/_search_results.html", {'papers': page_obj, 'search_score_limit': 0, 'show_topic_score': True})

    return HttpResponseNotFound()


def topic_overview(request):
    return render(request, "core/topic_overview.html", {'topics': Topic.objects.all()})


def imprint(request):
    return render(request, "core/imprint.html")

