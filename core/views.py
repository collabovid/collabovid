from django.shortcuts import render, HttpResponse
from django.templatetags.static import static

from scrape.scrape_data import get_data
from data.models import Paper

def home(request):

    all_papers = Paper.objects.all()

    paper_dicts = list()

    for paper in all_papers:
        paper_dicts.append(paper.to_dict())

    return render(request, "core/home.html", {'papers': paper_dicts})

def about(request):
    return render(request, "core/about.html")

def scrape(request):
    get_data(count=5)
    return HttpResponse("Scrape successfully.")
