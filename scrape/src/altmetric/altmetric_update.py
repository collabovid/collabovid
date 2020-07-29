import time
from math import ceil

from django.utils import timezone
from pyaltmetric import Altmetric

from data.models import AltmetricData, DataSource


class AltmetricUpdate:
    QUERY_INTERVAL_SEC = 0.0

    def __init__(self, api_key):
        self.altmetric = Altmetric(api_key=api_key)
        self.last_query = None

    def update(self, paper):
        if self.last_query:
            elapsed_time_sec = time.time() - self.last_query
            if self.QUERY_INTERVAL_SEC > 0.0 and elapsed_time_sec < self.QUERY_INTERVAL_SEC:
                time.sleep(int(ceil(self.QUERY_INTERVAL_SEC - elapsed_time_sec)))

        if paper.data_source_value == DataSource.ARXIV:
            data = self.altmetric.arxiv(paper.doi[6:])
        else:
            data = self.altmetric.doi(paper.doi)

        self.last_query = time.time()

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

        paper.last_altmetric_update = timezone.now()
        paper.save(set_manually_modified=False)
