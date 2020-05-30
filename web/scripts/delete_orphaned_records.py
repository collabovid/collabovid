import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'web.settings_dev')

import django
django.setup()

from data.models import Author, Journal


def delete_orphaned_journals():
    deleted_journals = 0
    for journal in list(Journal.objects.all()):
        if journal.papers.count() == 0:
            journal.delete()
            deleted_journals += 1

    print(f"Deleted {deleted_journals}")


def delete_orphaned_authors():
    deleted_authors = 0
    for author in list(Author.objects.all()):
        if author.publications.count() == 0:
            author.delete()
            deleted_authors += 1

    print(f"Deleted {deleted_authors}")


if __name__ == '__main__':
    delete_orphaned_authors()
    delete_orphaned_journals()
