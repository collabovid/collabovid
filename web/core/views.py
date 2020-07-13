from django.shortcuts import render
from django.http import HttpResponseNotFound
from data.models import GeoCity, GeoCountry, Paper, Category, Topic
from statistics import PaperStatistics, CategoryStatistics
import json

from django.utils.timezone import datetime
import requests

from django.conf import settings
from search.request_helper import SimilarPaperRequestHelper
from django.shortcuts import get_object_or_404


def home(request):
    if request.method == "GET":
        statistics = PaperStatistics(Paper.objects.all())

        latest_date = Paper.objects.filter(published_at__lte=datetime.now().date()).latest('published_at').published_at

        most_recent_papers = Paper.objects.filter(published_at=latest_date)
        return render(request, "core/home.html", {'statistics': statistics,
                                                  'most_recent_papers': most_recent_papers.order_by('-created_at'),
                                                  'most_recent_paper_statistics': PaperStatistics(most_recent_papers),
                                                  'most_recent_paper_date': latest_date})


def paper(request, doi):
    current_paper = get_object_or_404(Paper, doi=doi)
    similar_request = SimilarPaperRequestHelper(doi, number_papers=10)
    similar_paper = []
    if not similar_request.error:
        similar_paper = similar_request.paginator.page(1)
    return render(request, "core/paper.html", {
        "paper": current_paper,
        "similar_papers": similar_paper,
        "error": similar_request.error
    })


def embedding_visualization(request, topic_pk=None, doi=None):
    topics = Topic.objects.order_by('name')
    topic_dict = {}
    for topic in topics:
        topic_dict[topic.pk] = [x['doi'] for x in topic.papers.values('doi')]
    categories = Category.objects.all()
    category_colors = {}
    for category in categories:
        category_colors[category.pk] = category.color

    context = {
        'topics': topics,
        'topic_dict': json.dumps(topic_dict),
        'categories': categories,
        'category_colors': json.dumps(category_colors),
        'atlas_image_url': settings.PAPER_ATLAS_IMAGES_FILE_URL,
        'paper_file_url': settings.EMBEDDINGS_FILE_URL
    }

    if topic_pk:
        topic = get_object_or_404(Topic, pk=topic_pk)
        context['topic'] = topic
    elif doi:
        paper = get_object_or_404(Paper, pk=doi)
        context['paper'] = paper

    return render(request, "core/embedding_visualization.html", context)


def paper_cards(request):
    dois = request.GET.get('dois', None)
    if not dois:
        return HttpResponseNotFound()
    dois = json.loads(dois)
    papers = Paper.objects.filter(pk__in=dois)
    papers = sorted(papers, key=lambda x: dois.index(x.doi))
    return render(template_name="search/ajax/_search_results.html", request=request,
                  context={'papers': papers, 'show_score': False, 'use_paging': False})


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


def world_map(request):
    countries = GeoCountry.objects.all()

    countries = [
        {
            'pk': country.pk,
            'alpha2': country.alpha_2,
            'count': country.count,
            'displayname': country.displayname
        }
        for country in countries
    ]

    cities = GeoCity.objects.all()

    cities = [
        {
            'pk': city.pk,
            'name': city.name,
            'longitude': city.longitude,
            'latitude': city.latitude,
            'count': city.count,
            'displayname': city.displayname
        }
        for city in cities
    ]

    total_loc_related = Paper.objects.exclude(locations=None).count()
    top_countries = GeoCountry.objects.order_by('-count')[:3]

    return render(
        request,
        "core/map.html",
        {
            "countries": json.dumps(countries),
            "cities": json.dumps(cities),
            "total_loc_related": total_loc_related,
            "top_countries": [
                {
                    "name": x.alias,
                    "count": x.count
                }

                for x in top_countries]
        }
    )
