import os

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'web.settings_dev')
import django

django.setup()

from data.models import Paper

if __name__ == '__main__':
    Paper.objects.all().update(manually_modified=False)