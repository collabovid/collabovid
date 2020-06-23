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


def search(request):
    if request.method == "GET":
        semantic_paper_search = get_semantic_paper_search()
        if not wait_until(semantic_paper_search.is_ready):
            return HttpResponseBadRequest("Semantic Paper Search is not initialized yet")

        score_min = float(request.GET.get("score_min", "0"))

        form = json.loads(request.GET.get('form'))

        print(form)
        categories = form['categories']
        start_date = form['published_at_start']
        end_date = form['published_at_end']

        authors = form["authors"]
        journals = form["journals"]
        locations = form["locations"]
        search_query = form["query"].strip()

        authors_connection = form["authors_connection"]

        article_type_string = form["article_type"]

        article_type = SearchEngine.ARTICLE_TYPE_ALL

        if article_type_string == 'reviewed':
            article_type = SearchEngine.ARTICLE_TYPE_PEER_REVIEWED
        elif article_type_string == 'preprints':
            article_type = SearchEngine.ARTICLE_TYPE_PREPRINTS

        search_engine = get_default_search_engine()

        search_result = search_engine.search(search_query, start_date=start_date,
                                             end_date=end_date, score_min=score_min, author_ids=authors,
                                             author_and=(authors_connection == 'all'), journal_ids=journals,
                                             category_ids=categories, article_type=article_type, location_ids=locations)

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
