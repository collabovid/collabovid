from data.models import GeoCity, GeoCountry, GeoLocationMembership, GeoNameResolution, VerificationState
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
        name_resolutions = {x.source_name: x.target_name for x in GeoNameResolution.objects.iterator()}
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

        for location, usage, country in locations:
            word = usage['word'].strip()

            # Add the country (possibly the location) or the country that contains the location
            try:
                db_country = GeoCountry.objects.get(alpha_2=location.country_code)
                created = False
            except GeoCountry.DoesNotExist:
                db_country = GeoCountry.objects.create(
                    name=country.name,
                    alpha_2=country.country_code,
                    latitude=country.latitude,
                    longitude=country.longitude,
                )
                created = True

            if location.feature_label.startswith('A.PCL'):
                db_location = db_country
            else:
                db_location, created = GeoCity.objects.get_or_create(
                    name=location.name,
                    country=db_country,
                    latitude=location.latitude,
                    longitude=location.longitude,
                )

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
