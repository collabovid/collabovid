from django.http import JsonResponse, HttpResponse, HttpResponseServerError, HttpResponseBadRequest
from src.search.search_engine import get_default_search_engine, SearchEngine
from src.analyze import get_analyzer, is_analyzer_initialized, is_analyzer_initializing, CouldNotLoadPaperMatrix

from threading import Thread

def search(request):
    if request.method == "GET":

        categories = request.GET.getlist('categories', None)
        start_date = request.GET.get("start_date", "")
        end_date = request.GET.get("end_date", "")
        score_min = float(request.GET.get("score_min", "0"))

        authors = request.GET.get("authors", None)
        journals = request.GET.get("journals", None)
        locations = request.GET.get("locations", None)

        try:
            if journals:
                journals = [int(pk) for pk in journals.split(',')]

            if authors:
                authors = [int(pk) for pk in authors.split(',')]

            if categories:
                categories = [int(pk) for pk in categories]

            if locations:
                locations = [int(pk) for pk in locations.split(',')]
        except ValueError:
            return HttpResponseBadRequest("Request is malformed")

        search_query = request.GET.get("search", "").strip()

        authors_connection = request.GET.get("authors_connection", "one")

        article_type_string = request.GET.get("article_type")

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


def startup_probe(request):
    if is_analyzer_initialized():
        try:
            matrix = get_analyzer().vectorizer.paper_matrix

        except CouldNotLoadPaperMatrix:
            return HttpResponseServerError("Could not load paper matrix file.")

        if matrix:
            return HttpResponse("OK")

        return HttpResponseServerError("Loaded matrix is empty.")

    if not is_analyzer_initializing():
        thread = Thread(target=get_analyzer)
        thread.start()

    return HttpResponseServerError("Analyzer is initializing.")
