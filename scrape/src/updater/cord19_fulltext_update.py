from data.models import PaperData
from .cord19_cache import Cord19Cache, Cord19CacheError


class Cord19FulltextUpdater:
    @staticmethod
    def update(papers, log=print):
        log("Update fulltext data using CORD-19 dataset")
        cache = Cord19Cache()
        cache.refresh()

        count = 0
        count_abstract = 0

        for paper in papers:
            if not paper.data:
                if not paper.abstract:
                    metadata = cache.get_metadata(paper.doi)
                    if metadata and metadata['abstract']:
                        paper.abstract = metadata['abstract']
                        paper.save()
                        count_abstract += 1

                try:
                    fulltext = cache.fulltext(doi=paper.doi)
                    if fulltext:
                        paper.data = PaperData.objects.create(content=fulltext)
                        paper.save()
                        count += 1
                except Cord19CacheError:
                    continue

        log(f"Updated {count} fulltext data records")
        log(f"Updated {count_abstract} abstract data records")
