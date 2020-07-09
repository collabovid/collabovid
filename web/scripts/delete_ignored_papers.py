import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'web.settings_dev')

import django
django.setup()

from data.models import IgnoredPaper, Paper


def delete_ignored_papers():
    for ignored_paper in IgnoredPaper.objects.all():
        Paper.objects.filter(doi=ignored_paper.doi).delete()


if __name__ == '__main__':
    delete_ignored_papers()