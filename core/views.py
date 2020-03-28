from django.shortcuts import render, HttpResponse, get_object_or_404, reverse
from django.http import HttpResponseNotFound
from django.db.models import Q
from django.utils.dateparse import parse_date

from scrape.scrape_data import get_data
from data.models import Paper, Category, Topic


def home(request):
    papers = Paper.objects.all()
    categories = Category.objects.all()

    return render(request, "core/home.html",
                  {'papers': papers, 'categories': categories, 'search_url': reverse("search")})


def search(request):
    """
    Returns a (HTML) list of the requested papers.
    :param request:
    :return:
    """
    if request.method == "POST":
        category_names = request.POST.getlist("categories")
        search_query = request.POST.get("search", "")

        start_date = request.POST.get("published_at_start", "")
        end_date = request.POST.get("published_at_end", "")

        categories = Category.objects.filter(name__in=category_names)

        papers = Paper.get_paper_for_query(search_query, start_date, end_date, categories)

        return render(request, "core/partials/_search_results.html", {'papers': papers})

    return HttpResponseNotFound()


def about(request):
    return render(request, "core/about.html")


def scrape(request):
    get_data(count=50)
    return HttpResponse("Scrape successfully.")


def topic(request, id):
    topic = get_object_or_404(Topic, pk=id)

    if request.method == "GET":
        categories = set()
        for paper in topic.papers.all():
            categories.add(paper.category)

        return render(request, "core/topic.html",
                      {'topic': topic, 'categories': categories, 'search_url': reverse("topic", args=(topic.pk,))})

    elif request.method == "POST":

        category_names = request.POST.getlist("categories")
        search_query = request.POST.get("search", "")

        start_date = request.POST.get("published_at_start", "")
        end_date = request.POST.get("published_at_end", "")

        categories = Category.objects.filter(name__in=category_names)

        papers = Paper.get_paper_for_query(search_query, start_date, end_date, categories).filter(topic=topic)

        return render(request, "core/partials/_search_results.html", {'papers': papers})

    return HttpResponseNotFound()


def topic_overview(request):
    return render(request, "core/topic_overview.html", {'topics': Topic.objects.all()})
