import pycountry

from data.models import GeoCity, GeoCountry, GeoLocation, GeoLocationMembership, GeoNameResolution, VerificationState
from src.geo.geo_parser import GeoParser


class PaperGeoExtractor:
    """
    This class extracts geo locations for given papers. It is doing so
    by using the GeoParser class to extract locations from the paper's title.
    """
    LOCATION_CREATED = 0
    LOCATION_ADDED = 1
    LOCATION_SKIPPED = 2

    def __init__(self, db_path):
        name_resolutions = {x.source_name: x.target_geonames_id for x in GeoNameResolution.objects.iterator()}
        self.geo_parser = GeoParser(db_path=db_path, name_resolutions=name_resolutions)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def close(self):
        self.geo_parser.close()

    def extract_locations(self, paper, recompute_count=True):
        locations, ignored_entities = self.geo_parser.parse(paper.title, merge=True)
        creation_states = []

        for location, usage in locations:
            word = usage['word'].strip()

            db_location, created = GeoLocation.get_or_create_from_geonames_object(location)

            if not paper.locations.filter(pk=db_location.pk).exists():

                membership = GeoLocationMembership()
                membership.paper = paper
                membership.location = db_location
                membership.word = word
                membership.state = VerificationState.AUTOMATICALLY_ACCEPTED
                membership.prevent_recompute_count = not recompute_count
                membership.save()

                state = PaperGeoExtractor.LOCATION_CREATED if created else PaperGeoExtractor.LOCATION_ADDED
            else:
                state = PaperGeoExtractor.LOCATION_SKIPPED

            creation_states.append((db_location, word, state))
        return creation_states, ignored_entities
