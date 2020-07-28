from time import sleep
from datetime import timedelta
from timeit import default_timer as timer

from django.utils.datetime_safe import datetime
from pyaltmetric import Altmetric

from data.models import AltmetricData, DataSource


class AltmetricUpdate:
    QUERY_INTERVAL_SEC = 1

    def __init__(self, api_key):
        self.altmetric = Altmetric(api_key=api_key)
        self.last_query = None

    def update(self, paper):
        if self.last_query:
            elapsed_time_sec = timedelta(seconds=timer() - self.last_query).total_seconds()
            if elapsed_time_sec < self.QUERY_INTERVAL_SEC:
                sleep(self.QUERY_INTERVAL_SEC - elapsed_time_sec)

        if paper.data_source_value == DataSource.ARXIV:
            data = self.altmetric.arxiv(paper.doi[6:])
        else:
            data = self.altmetric.doi(paper.doi)

        self.last_query = timer()

        if data and data['score'] > 0.0:
            if not paper.altmetric_data:
                paper.altmetric_data = AltmetricData.objects.create()

            paper.altmetric_data.score = data['score']
            paper.altmetric_data.score_d = data['history']['1d']
            paper.altmetric_data.score_w = data['history']['1w']
            paper.altmetric_data.score_1m = data['history']['1m']
            paper.altmetric_data.score_3m = data['history']['3m']
            paper.altmetric_data.score_6m = data['history']['6m']
            paper.altmetric_data.score_y = data['history']['1y']
            paper.altmetric_data.save()

        paper.last_altmetric_update = datetime.now()
        paper.save()
