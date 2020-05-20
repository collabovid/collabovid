from django.contrib.admin.views.decorators import staff_member_required
from django.http import HttpResponse, HttpResponseNotFound
from django.shortcuts import render

from data.models import Paper, PaperState


@staff_member_required
def data_sanitizing(request):
    if request.method == "GET":
        papers = Paper.objects.filter(paper_state=PaperState.UNKNOWN)[:100]
        return render(request, "scrape/paper_table.html", {"papers": papers})
    elif request.method == "POST":
        doi = request.POST.get('doi', '')
        new_state = request.POST.get('state', '')

        if doi and new_state:
            try:
                paper = Paper.objects.get(doi=doi)
                if new_state in [PaperState.UNKNOWN, PaperState.VERIFIED, PaperState.BULLSHIT]:
                    # paper.paper_state = new_state
                    print(f"Set state of {paper.doi} to {new_state}")
                    return HttpResponse('')
                else:
                    return HttpResponseNotFound('Invalid state')
            except Paper.DoesNotExist:
                return HttpResponseNotFound('DOI not found.')
