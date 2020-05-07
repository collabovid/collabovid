from django.http import JsonResponse
from src.search.search_engine import get_default_search_engine


def search(request):
    if request.method == "GET":
        category_names = request.GET.getlist("categories")

        start_date = request.GET.get("published_at_start", "")
        end_date = request.GET.get("published_at_end", "")

        # tab = request.GET.get("tab", "")

        search_query = request.GET.get("search", "").strip()
        search_engine = get_default_search_engine()

        search_result = search_engine.search(search_query, categories=category_names, start_date=start_date,
                                             end_date=end_date, score_min=0.65)

        return JsonResponse(search_result)
