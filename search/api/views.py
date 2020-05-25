from django.http import JsonResponse, HttpResponse, HttpResponseServerError
from src.search.search_engine import get_default_search_engine
from src.analyze import get_analyzer, is_analyzer_initialized, is_analyzer_initializing, CouldNotLoadPaperMatrix

from threading import Thread
import json


def search(request):
    if request.method == "GET":
        start_date = request.GET.get("start_date", "")
        end_date = request.GET.get("end_date", "")
        score_min = float(request.GET.get("score_min", "0"))

        authors = json.loads(request.GET.get("authors", "[]"))
        authors = [a["value"] for a in authors]

        search_query = request.GET.get("search", "").strip()

        authors_connection = request.GET.get("authors_connection", "one")

        search_engine = get_default_search_engine()

        search_result = search_engine.search(search_query, start_date=start_date,
                                             end_date=end_date, score_min=score_min, author_names=authors,
                                             author_and=(authors_connection == 'all'))

        return JsonResponse(search_result)


def startup_probe(request):
    if is_analyzer_initialized():
        try:
            matrix = get_analyzer().vectorizer.paper_matrix

        except CouldNotLoadPaperMatrix:
            return HttpResponseServerError()

        if matrix:
            return HttpResponse("OK")

        return HttpResponseServerError()

    if not is_analyzer_initializing():
        thread = Thread(target=get_analyzer)
        thread.start()

    return HttpResponseServerError()
