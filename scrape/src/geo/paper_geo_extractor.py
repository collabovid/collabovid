from data.models import GeoCity, GeoCountry, GeoLocation, GeoLocationMembership, GeoStopword, VerificationState
from src.geo.country_data import CountryData
from src.geo.geo_parser import GeoParser


class PaperGeoExtractor:
    LOCATION_CREATED = 0
    LOCATION_ADDED = 1
    LOCATION_SKIPPED = 2

    def __init__(self, db_path):
        self.geo = GeoParser(db_path=db_path)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def close(self):
        self.geo.close()

    def extract_locations(self, paper):
        locations, ignored_entities = self.geo.parse(paper.title, merge=True)
        creation_states = []

        for location, usage in locations:
            word = usage['word'].strip()

            if GeoStopword.objects.filter(word=word.lower()).exists():
                ignored_entities.append(word)
                continue

            country_data = CountryData.get(location.country_code)
            db_country, created = GeoCountry.objects.get_or_create(
                name=country_data['name'],
                alias=country_data['alias'],
                alpha_2=location.country_code,
                latitude=country_data['lat'],
                longitude=country_data['lon'],
            )

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
                GeoLocationMembership.objects.create(
                    paper=paper,
                    location=db_location,
                    word=word,
                    state=VerificationState.AUTOMATICALLY_ACCEPTED,
                )
                state = PaperGeoExtractor.LOCATION_CREATED if created else PaperGeoExtractor.LOCATION_ADDED
            else:
                state = PaperGeoExtractor.LOCATION_SKIPPED

            creation_states.append((db_location, word, state))
        return creation_states, ignored_entities
