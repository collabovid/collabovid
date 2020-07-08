from django.http import JsonResponse, HttpResponse, HttpResponseServerError, HttpResponseBadRequest

from data.models import Paper
from src.search.search_engine import SearchEngine
from src.analyze import get_semantic_paper_search, get_similar_paper_finder
import time
import json

from src.search.utils import TimerUtilities
from src.search.virtual_paginator import VirtualPaginator
from collections import defaultdict
import heapq

def wait_until(condition, interval=0.1, timeout=10):
    start = time.time()
    while not condition() and time.time() - start < timeout:
        time.sleep(interval)
    return condition()


def search(request):
    if request.method == "GET":
        semantic_paper_search = get_semantic_paper_search()
        if not wait_until(semantic_paper_search.is_ready):
            return HttpResponseBadRequest("Semantic Paper Search is not initialized yet")

        form = json.loads(request.GET.get('form'))
        search_engine = SearchEngine(form)
        search_result = TimerUtilities.time_function(search_engine.search)

        if form['result_type'] == 'papers':
            paginator = VirtualPaginator(search_result, form)
            page = TimerUtilities.time_function(paginator.get_page)

            return JsonResponse(page)
        elif form['result_type'] == 'statistics':
            return JsonResponse({'results': list(search_result.keys())})

        return HttpResponseBadRequest()


def similar(request):
    """
    Api method to retrieve the most similar paper given a doi.
    :param request: Request containing the doi as a HTTP GET parameter
    :return: json response with the list of papers and the corresponding similarity score
    """
    if request.method == "GET":
        paper_finder = get_similar_paper_finder()
        if not wait_until(paper_finder.is_ready):
            return HttpResponseBadRequest("Similar Paper finder is not initialized yet")

        dois = request.GET.getlist('dois')
        limit = int(request.GET.get('limit'))

        dois = list(Paper.objects.filter(pk__in=dois).values_list('doi', flat=True))

        print(dois)

        doi_scores = defaultdict(int)
        for doi in dois:
            similar_paper = paper_finder.similar(doi)
            for doi, score in similar_paper:
                doi_scores[doi] += score

        result = []

        flattened_score_dict = list(doi_scores.items())
        print(flattened_score_dict)

        for doi, score in heapq.nlargest(limit, flattened_score_dict, key=lambda x: x[1]):
            result.append({
                'doi': doi,
                'score': score
            })
            print(doi, score)

        return JsonResponse({'similar': result})
    return HttpResponseBadRequest("Only Get is allowed here")


def startup_probe(request):
    paper_finder = get_similar_paper_finder()
    paper_search = get_semantic_paper_search()

    if not paper_finder.is_ready():
        return HttpResponseServerError("Similar Paper finder not ready.")

    if not paper_search.is_ready():
        return HttpResponseServerError("Semantic Paper Search not ready.")

    return HttpResponse("OK")
