import os

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'web.settings_dev')

import django

django.setup()

from data.models import Author, Paper


def set_vectorized():
    Paper.objects.all().update(vectorized=True)


if __name__ == '__main__':
    print('setting all papers to vectorized=True')
    set_vectorized()
    print('Done with update.')
