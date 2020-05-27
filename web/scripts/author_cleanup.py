import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'web.settings_dev')

import django
django.setup()

from django.db import transaction
from data.models import Author, Paper


def sanitize_author_duplicates():
    for paper in Paper.objects.all():
        with transaction.atomic():
            authors = list(paper.authors.all())
            paper.authors.clear()
            for author in authors:
                duplicates = list(Author.objects.filter(
                    last_name=author.last_name,
                    first_name=author.first_name,
                ))
                if len(duplicates) > 1:
                    min_pk_idx = min(
                        range(len(duplicates)), key=lambda x: duplicates[x].pk
                    )
                    min_pk_author = duplicates[min_pk_idx]
                    print(f"Delete duplicate authors: {author.first_name} {author.last_name}")
                else:
                    min_pk_author = author
                paper.authors.add(min_pk_author)
            paper.save()


def delete_unused_authors():
    deleted_authors = 0
    for author in list(Author.objects.all()):
        if author.publications.count() == 0:
            author.delete()
            deleted_authors += 1

    print(f"Removed {deleted_authors}")


if __name__ == '__main__':
    sanitize_author_duplicates()
    delete_unused_authors()