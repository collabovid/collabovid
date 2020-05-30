import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'web.settings_dev')

import django
django.setup()

from data.models import Paper


def delete_publishing_date_none():
    deleted_papers = 0
    for paper in list(Paper.objects.all()):
        if paper.published_at is None:
            paper.delete()
            deleted_papers += 1

    print(f"Deleted {deleted_papers}")


if __name__ == '__main__':
    delete_publishing_date_none()