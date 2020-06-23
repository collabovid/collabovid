from django.http import JsonResponse, HttpResponse, HttpResponseServerError, HttpResponseBadRequest
from src.search.search_engine import get_default_search_engine, SearchEngine
from src.analyze import get_semantic_paper_search, get_similar_paper_finder
import time
import json


def wait_until(condition, interval=0.1, timeout=10):
    start = time.time()
    while not condition() and time.time() - start < timeout:
        time.sleep(interval)
    return condition()


def search_similar(request):
    if request.method == "GET":
        score_min = float(request.GET.get("score_min", "0"))
        form = json.loads(request.GET.get('form'))

        filtered, filtered_papers = SearchEngine.filter_papers(form)

        print(form)

        result = dict()

        for doi in filtered_papers.values_list('doi', flat=True):
            result[doi] = 0

        paper_finder = get_similar_paper_finder()
        if not wait_until(paper_finder.is_ready):
            return HttpResponseBadRequest("Similar Paper finder is not initialized yet")

        if form['similar_papers']:
            similar_factor = 1/len(form['similar_papers'])
            for paper_doi in form['similar_papers']:
                similar_paper = paper_finder.similar(paper_doi)
                for doi, score in similar_paper:
                    if doi in result:
                        result[doi] += score * similar_factor

        if form['different_papers']:
            different_factor = 1 / len(form['different_papers'])
            for paper_doi in form['different_papers']:
                similar_paper = paper_finder.similar(paper_doi)
                for doi, score in similar_paper:
                    if doi in result:
                        result[doi] -= score * different_factor

        #result = {key: val for key, val in result.items() if val > score_min}

        return JsonResponse(result)


def search(request):
    if request.method == "GET":
        semantic_paper_search = get_semantic_paper_search()
        if not wait_until(semantic_paper_search.is_ready):
            return HttpResponseBadRequest("Semantic Paper Search is not initialized yet")

        score_min = float(request.GET.get("score_min", "0"))

        form = json.loads(request.GET.get('form'))
        search_engine = get_default_search_engine()

        search_result = search_engine.search(form, score_min=score_min)

        return JsonResponse(search_result)


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

        doi = request.GET.get('doi')
        limit = request.GET.get('limit')
        similar_paper = paper_finder.similar(doi, top=limit)
        result = []
        for doi, score in similar_paper:
            result.append({
                'doi': doi,
                'score': score
            })
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
