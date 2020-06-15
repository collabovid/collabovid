import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'web.settings_dev')

import django
django.setup()

from data.models import GeoStopword

def load_initial_stopwords():
    stopwords = ['md', 'ct', 'ms', 'awake', 'multi', 'las', 'mobile', 'ksa', 'cross', 'stan', 'st', 'gis']

    for word in stopwords:
        GeoStopword.objects.create(word=word)

if __name__ == '__main__':
    load_initial_stopwords()