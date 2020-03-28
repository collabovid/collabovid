from django.shortcuts import render, HttpResponse
from django.http import HttpResponseNotFound
from django.db.models import Q
from django.utils.dateparse import parse_date

from scrape.scrape_data import get_data
from data.models import Paper, Category


def home(request):
    papers = Paper.objects.all()
    categories = Category.objects.all()

    return render(request, "core/home.html", {'papers': papers, 'categories': categories})


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

        try:
            start_date = parse_date(start_date)
        except ValueError:
            start_date = None

        try:
            end_date = parse_date(end_date)
        except ValueError:
            end_date = None

        categories = Category.objects.filter(name__in=category_names)
        papers = Paper.objects.filter(Q(category__in=categories) & (Q(title__contains=search_query) |
                                                                    Q(authors__first_name__contains=search_query) |
                                                                    Q(authors__last_name__contains=search_query))
                                      ).distinct()

        if start_date:
            papers = papers.filter(published_at__gte=start_date)

        if end_date:
            papers = papers.filter(published_at__lte=end_date)

        return render(request, "core/partials/_search_results.html", {'papers': papers})

    return HttpResponseNotFound()


def about(request):
    return render(request, "core/about.html")


def scrape(request):
    get_data(count=5)
    return HttpResponse("Scrape successfully.")
