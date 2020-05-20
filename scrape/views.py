from django.http import HttpResponseNotFound, HttpResponse
from django.shortcuts import render
from django.contrib.admin.views.decorators import staff_member_required
from data.models import Paper, PaperState


@staff_member_required
def data_sanitizing(request):
    if request.method == "GET":
        papers = Paper.objects.filter(paper_state=PaperState.UNKNOWN)[:100]
        return render(request, "scrape/paper_table.html", {"papers": papers})
    elif request.method == "POST":
        doi = request.POST.get('doi', '')
        action = request.POST.get('action', '')

        if doi and action:
            try:
                paper = Paper.objects.get(doi=doi)
                valid_actions = {'unknown': PaperState.UNKNOWN, 'accept': PaperState.VERIFIED,
                                 'decline': PaperState.BULLSHIT}
                if action in valid_actions:
                    print(f"Set state of {paper.doi} to {action}")
                    paper.paper_state = valid_actions[action]
                    return HttpResponse('')
                else:
                    return HttpResponseNotFound('Invalid action')
            except Paper.DoesNotExist:
                return HttpResponseNotFound('DOI not found.')
        return HttpResponseNotFound
