import os

import django


os.environ.setdefault("DJANGO_SETTINGS_MODULE", "covid19_publications.settings")
django.setup()

from scrape.updater.medrxiv_update import MedrxivUpdater
from scrape.updater.cord19_update import Cord19Updater

if __name__ == '__main__':
    updater = Cord19Updater(log=print)
    #updater = MedrxivUpdater(log=print)
    updater.update(max_count=0, pdf_content=False)