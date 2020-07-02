from django.conf import settings

from data.models import GeoCity, GeoCountry, GeoLocation, Paper
from src.geo.paper_geo_extractor import PaperGeoExtractor
from tasks.definitions import register_task, Runnable

from tasks.colors import Green, Red, Grey


@register_task
class GeoParserTask(Runnable):
    @staticmethod
    def task_name():
        return 'parse-geo-locations'

    @staticmethod
    def description():
        return ''

    def __init__(self, *args, **kwargs):
        super(GeoParserTask, self).__init__(*args, **kwargs)

    def run(self):
        n_locations = 0

        with PaperGeoExtractor(db_path=f'{settings.GEONAMES_DB_PATH}') as geo:
            for paper in self.progress(Paper.objects.filter(location_modified=False)):
                locations, ignored_entities = geo.extract_locations(paper, recompute_count=False)
                locations = [x for x in locations if x[2] != PaperGeoExtractor.LOCATION_SKIPPED]
                n_locations += len(locations)

                if len(locations) > 0 or len(ignored_entities) > 0:
                    self.log(paper.title)

                    for location in locations:
                        state = 'created' if location[2] == PaperGeoExtractor.LOCATION_CREATED else 'added'
                        self.log(
                            "\t[", Green(state), "]\t{} -> {}".format(location[1], location[0].name)
                        )

                    for ent in ignored_entities:
                        self.log("\t[", Red('ignored'), "]\t{}".format(ent))

            self.log(Grey("Recomputing counts."))
            GeoLocation.recompute_counts(GeoCity.objects.all(), GeoCountry.objects.all())
            self.log(Green("Recomputed counts"))

        self.log(f"Added {n_locations} locations")
