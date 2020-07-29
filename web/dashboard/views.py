import json
from time import strftime

from django.conf import settings
from django.db import transaction, IntegrityError
from django.http import HttpResponseNotFound, HttpResponse, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404

from collabovid_store.s3_utils import S3BucketClient
from dashboard.forms import PaperForm
from data.models import (
    Author,
    AuthorNameResolution,
    AuthorPaperMembership, DeleteCandidate,
    GeoCity,
    GeoLocation,
    GeoCountry,
    GeoLocationMembership,
    GeoNameResolution,
    IgnoredPaper,
    Journal,
    Paper,
    ScrapeConflict,
)
from geolocations.geoname_db import GeonamesDBError
from search.models import SearchQuery
from tasks.models import Task
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from datetime import timedelta, datetime
from django.utils import timezone
from tasks.launcher.task_launcher import get_task_launcher

from tasks.load import AVAILABLE_TASKS, get_task_by_id
from geolocations.location_modifier import LocationModifier

import os


@staff_member_required
def queries(request):
    queries = SearchQuery.objects.order_by('-created_at')[:100]
    return render(request, "dashboard/queries/overview.html",
                  {'search_queries': queries, 'total': SearchQuery.objects.count()})


@staff_member_required
def tasks(request):
    tasks = Task.objects.order_by('-started_at').defer('log')
    return render(request, 'dashboard/tasks/task_overview.html', {'tasks': tasks, 'debug': settings.DEBUG})


@staff_member_required
def task_detail(request, id):
    task = Task.objects.get(pk=id)
    return render(request, 'dashboard/tasks/task_detail.html', {'task': task, 'debug': settings.DEBUG})


@staff_member_required
def select_task(request):
    if request.method == 'GET':
        return render(request, 'dashboard/tasks/task_select.html',
                      {'services_with_tasks': AVAILABLE_TASKS, 'debug': settings.DEBUG})

    return HttpResponseNotFound()


@staff_member_required
def create_task(request, task_id):
    service, task_definition = get_task_by_id(task_id)

    if service and task_definition:
        if request.method == 'GET':
            return render(request, 'dashboard/tasks/task_create.html',
                          {'task_id': task_id, 'definition': task_definition, 'debug': settings.DEBUG})
        elif request.method == 'POST':

            task_launcher = get_task_launcher(service)

            task_config = {
                'service': service,
                'parameters': [],
                'started_by': request.user.username
            }

            for parameter in task_definition['parameters']:
                if parameter['is_primitive']:
                    task_config['parameters'].append(
                        {
                            'name': parameter['name'],
                            'type': parameter['type'],
                            'value': request.POST.get(parameter['name'], parameter['default'])
                        }
                    )

            result = task_launcher.launch_task(name=task_id, config=task_config, block=False)

            if result:
                messages.add_message(request, messages.SUCCESS, 'Task started.')
            else:
                messages.add_message(request, messages.ERROR, 'Some exception was thrown when starting the task.')
            return redirect('tasks')

    return HttpResponseNotFound()


@staff_member_required
def delete_task(request):
    if request.method == 'POST':
        id = request.POST.get('id')
        print(id)
        query = Task.objects.filter(pk=id)
        if query.count() > 0:
            query.delete()
            messages.add_message(request, messages.SUCCESS, 'Deleted Task.')
        else:
            messages.add_message(request, messages.ERROR, 'Failed to delete Task: Unknown Task.')
        return redirect('tasks')
    return HttpResponseNotFound()


@staff_member_required
def delete_all_finished(request):
    if request.method == 'POST':
        days = 1
        date_limit = timezone.now() - timedelta(days=days)
        query = Task.objects.filter(ended_at__lte=date_limit).defer('log')
        if query.count() > 0:
            query.delete()
            messages.add_message(request, messages.SUCCESS, 'Deleted All Finished Tasks.')
        else:
            messages.add_message(request, messages.WARNING, 'No Tasks to delete.')
        return redirect('tasks')
    return HttpResponseNotFound()


@staff_member_required
def show_location(request, id):
    if request.method == 'GET':
        country = get_object_or_404(GeoCountry, pk=id)

        return render(request, 'dashboard/locations/country.html',
                      {'country': country, 'debug': settings.DEBUG})


@staff_member_required
def delete_location(request, location_id):
    if request.method == 'POST':
        if location_id:
            try:
                location = GeoLocation.objects.get(pk=location_id)
                LocationModifier.delete_and_ignore_location(location)
                messages.add_message(request, messages.SUCCESS, f"Successfully deleted location {location.name}")
            except GeoLocation.DoesNotExist:
                messages.add_message(request, messages.ERROR, f"No location with id{location_id}")
    return redirect('locations')


@staff_member_required
def delete_location_membership(request):
    if request.method == 'POST':
        location_id = request.POST.get('location')
        paper_id = request.POST.get('paper')

        if LocationModifier.delete_location_membership(location_id, paper_id):
            messages.add_message(request, messages.SUCCESS, "Deleted location membership")
        else:
            messages.add_message(request, messages.ERROR,
                                 "No location membership (Maybe the paper is related to a city within that country)"
                                 )
        return redirect('locations')


@staff_member_required
def edit_location(request, location_id):
    location = GeoLocation.objects.get(pk=location_id)
    if request.method == 'GET':
        selected_paper_doi = request.GET.get("paper")
        if selected_paper_doi:
            try:
                membership = GeoLocationMembership.objects.get(location_id=location_id, paper_id=selected_paper_doi)
            except GeoLocationMembership.DoesNotExist:
                messages.add_message(request, messages.ERROR,
                                     "No location membership (Maybe the paper is related to a city within that country)"
                                     )
                return redirect('locations')
        else:
            membership = None
        return render(
            request, 'dashboard/locations/edit_location.html',
            {'location': location, 'membership': membership, 'debug': settings.DEBUG}
        )
    elif request.method == 'POST':
        new_geonames_id = request.POST.get("geonames_id", None)
        if not new_geonames_id:
            messages.add_message(request, messages.ERROR, f"New Geonames ID not specified")
            return redirect('locations')
        location = GeoLocation.objects.get(pk=location_id)
        try:
            new_location = LocationModifier.change_location(location, new_geonames_id)
            messages.add_message(request, messages.SUCCESS,
                                 f"Successfully changed location from {location.name} to {new_location.name}")
        except GeonamesDBError as ex:
            messages.add_message(request, messages.ERROR, ex)
        return redirect('locations')


@staff_member_required
def add_location(request, doi):
    paper = Paper.objects.get(doi=doi)
    if request.method == 'GET':
        return render(request, 'dashboard/locations/add_location.html', {'paper': paper, 'debug': settings.DEBUG})
    elif request.method == 'POST':
        geonames_id = request.POST.get("geonames_id", None)
        if not geonames_id:
            messages.add_message(request, messages.ERROR, f"Geonames ID not specified")
            return redirect('add_location', doi=doi)

        try:
            location = LocationModifier.add_location(paper, geonames_id)
            messages.add_message(request, messages.SUCCESS,
                                 f"Successfully added location {location.name} to {doi}")
        except GeonamesDBError as ex:
            messages.add_message(request, messages.ERROR, ex)
            return redirect('add_location', doi=doi)
        return redirect('paper', doi=doi)


@staff_member_required
def locations(request):
    if request.method == 'GET':
        countries = GeoCountry.objects.all()
        cities = GeoCity.objects.all()
        name_resolutions = GeoNameResolution.objects.all()

        return render(request, 'dashboard/locations/locations.html',
                      {'countries': countries, 'cities': cities, 'name_resolutions': name_resolutions,
                       'debug': settings.DEBUG})


# @staff_member_required
# def data_sanitizing(request):
#     if request.method == "GET":
#         papers = Paper.objects.filter(paper_state=PaperState.UNKNOWN)[:100]
#         return render(request, "dashboard/scrape/paper_table.html", {"papers": papers, 'debug': settings.DEBUG})
#     elif request.method == "POST":
#         doi = request.POST.get('doi', '')
#         action = request.POST.get('action', '')
#
#         if doi and action:
#             try:
#                 paper = Paper.objects.get(doi=doi)
#                 valid_actions = {'unknown': PaperState.UNKNOWN, 'accept': PaperState.VERIFIED,
#                                  'decline': PaperState.BULLSHIT}
#                 if action in valid_actions:
#                     print(f"Set state of {paper.doi} to {action}")
#                     paper.paper_state = valid_actions[action]
#                     paper.save()
#                     return HttpResponse('')
#                 else:
#                     return HttpResponseNotFound('Invalid action')
#             except Paper.DoesNotExist:
#                 return HttpResponseNotFound('DOI not found.')
#         return HttpResponseNotFound()


@staff_member_required
def data_import(request):
    s3_client = S3BucketClient(
        aws_access_key=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        endpoint_url=settings.AWS_S3_ENDPOINT_URL,
        bucket=settings.AWS_STORAGE_BUCKET_NAME,
    )

    if settings.DB_EXPORT_STORE_LOCALLY:
        import_archives = os.listdir(settings.DB_EXPORT_LOCAL_DIR)
    else:
        import_archives = s3_client.all_objects(prefix=settings.S3_DB_EXPORT_LOCATION)

    sorted_archives = sorted([os.path.basename(x) for x in import_archives if x.endswith('.tar.gz')], reverse=True)

    return render(request, 'dashboard/data_import/data_import_overview.html',
                  {'archives': sorted_archives, 'debug': settings.DEBUG})


@staff_member_required
def delete_archive(request, archive_path):
    if request.method == 'POST':
        filename = archive_path
        if filename:
            if settings.DB_EXPORT_STORE_LOCALLY:
                file_path = os.path.join(settings.DB_EXPORT_LOCAL_DIR, filename)
                if os.path.exists(file_path):
                    messages.add_message(request, messages.SUCCESS, f"Deleted {filename}")
                    os.remove(file_path)
                else:
                    messages.add_message(request, messages.ERROR, f"File: {file_path} does not exist")
            else:
                s3_client = S3BucketClient(
                    aws_access_key=settings.AWS_ACCESS_KEY_ID,
                    aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                    endpoint_url=settings.AWS_S3_ENDPOINT_URL,
                    bucket=settings.AWS_STORAGE_BUCKET_NAME,
                )
                s3_client.delete_file(filename)
                messages.add_message(request, messages.SUCCESS, f"Deleted {filename}")
        else:
            messages.add_message(request, messages.ERROR, 'Error: No filename specified')
        return redirect('data_import')
    return HttpResponseNotFound()


@staff_member_required
def location_sanitizing(request):
    location_papers = Paper.objects.exclude(locations=None)
    location_memberships = [
        {"paper": paper, "locations": GeoLocationMembership.objects.filter(paper_id=paper.doi)}
        for paper in location_papers
    ]

    return render(request, 'dashboard/sanitizing/location_sanitizing_overview.html',
                  {'location_papers': location_memberships, 'debug': settings.DEBUG})


@staff_member_required
def language_detection(request):
    if request.method == 'GET':
        candidates = DeleteCandidate.objects.filter(
            type=DeleteCandidate.Type.LANGUAGE, false_positive=False).order_by('-score').select_related('paper')
        return render(request, 'dashboard/language_detection/language_detection.html',
                      {'candidates': candidates, 'debug': settings.DEBUG})
    elif request.method == 'POST':
        paper_doi = request.POST.get('paper_doi')
        action = request.POST.get('action')

        if action == 'delete':
            paper = Paper.objects.get(doi=paper_doi)
            with transaction.atomic():
                paper.delete()
                IgnoredPaper.objects.create(doi=paper_doi)
        elif action == 'ignore':
            candidate = DeleteCandidate.objects.get(paper_id=paper_doi, type=DeleteCandidate.Type.LANGUAGE)
            candidate.false_positive = True
            candidate.save()
        else:
            return HttpResponseNotFound()

        return JsonResponse({'status': 'success'})


@staff_member_required
def scrape_conflict(request):
    if request.method == 'GET':
        errors = []
        for error in ScrapeConflict.objects.all():
            datapoint = json.loads(error.datapoint)
            form = PaperForm(instance=error.paper)
            comparison = {
                'publication_date': datetime.strftime(error.paper.published_at, '%Y-%m-%d') == datapoint['publication_date'],
                'authors': sorted([[a.last_name, a.first_name] for a in error.paper.authors.all()]) == sorted(datapoint['authors']),
                'journal': error.paper.journal.name == datapoint['journal'] if error.paper.journal else datapoint['journal'],
            }
            errors.append({'paper': error.paper, 'form': form, 'datapoint': json.loads(error.datapoint), 'comparison': comparison})

        return render(request, 'dashboard/scrape/scrape_conflicts_overview.html',
                      {'errors': errors, 'debug': settings.DEBUG})

    elif request.method == 'POST':
        doi = request.POST.get('doi')
        paper = Paper.objects.get(doi=doi)
        conflict = ScrapeConflict.objects.get(paper=paper)

        if 'accept-button' in request.POST:
            form = PaperForm(request.POST, instance=paper)
            if not form.is_valid():
                messages.add_message(request, messages.ERROR, f"{form.errors}")
            else:
                with transaction.atomic():
                    try:
                        form.save()
                        if request.POST.get('manually_modified') == 'on':
                            paper.manually_modified = True
                        else:
                            paper.manually_modified = False

                        AuthorPaperMembership.objects.filter(paper=paper).delete()
                        rank = 0
                        for author in request.POST.get('author_list').split(';'):
                            author, _ = Author.get_or_create_by_name(author.split(',')[1], author.split(',')[0])
                            if author is not None:
                                AuthorPaperMembership.objects.create(paper=paper, author=author, rank=rank)
                                rank += 1

                        journal_name = request.POST.get('journal_name', None)
                        if journal_name:
                            journal = Journal.objects.get_or_create(name=journal_name)
                        else:
                            journal = None
                        paper.journal = journal

                        paper.visualized = False
                        paper.vectorized = False

                        paper.scrape_hash = json.loads(conflict.datapoint)['_md5']
                        paper.save()
                        conflict.delete()
                        messages.add_message(request, messages.SUCCESS, "Successfully saved the changes.")
                    except IntegrityError:
                        messages.add_message(request, messages.ERROR, "Integrity error.")

        return redirect('scrape_conflict')


@staff_member_required
def change_author_name(request, author_id, doi=None):
    author = Author.objects.get(pk=author_id)

    if doi:
        current_paper = Paper.objects.get(doi=doi)
    else:
        current_paper = None

    def redirect_():
        return render(
            request,
            'dashboard/authors/add_name_resolution.html',
            {'author': author, 'current_paper': current_paper, 'debug': settings.DEBUG}
        )

    if request.method == 'GET':
        return redirect_()
    elif request.method == 'POST':
        action = request.POST.get('action')
        if action == 'save_all':
            AuthorNameResolution.add(author.first_name, author.last_name,
                                     request.POST.get('first_name'), request.POST.get('last_name'))
        elif action == 'delete_all':
            for paper in Paper.objects.filter(authors=author).all():
                if paper.authors.count() == 1:
                    messages.add_message(request, messages.ERROR, f"Cannot remove the only author of the paper \"{paper.title}\"")
                    return redirect_()
            AuthorNameResolution.ignore(author.first_name, author.last_name)
        elif action == 'delete_current':
            if current_paper.authors.count() == 1:
                messages.add_message(request, messages.ERROR, "Cannot remove the only author of this paper")
                return redirect_()
            AuthorPaperMembership.objects.get(author=author, paper=current_paper).delete()
            current_paper.manually_modified = True
            current_paper.save()
        else:
            return HttpResponseNotFound()

        return HttpResponse('Success')


@staff_member_required
def swap_all_author_names(request, doi):
    if request.method == 'POST':
        try:
            paper = Paper.objects.get(doi=doi)
            for author in paper.authors.all():
                AuthorNameResolution.add(author.first_name, author.last_name, author.last_name, author.first_name)
            return redirect('paper', doi=doi)
        except Paper.DoesNotExist:
            return HttpResponseNotFound(f"Unknown Paper {doi}")
    else:
        return HttpResponseNotFound()

