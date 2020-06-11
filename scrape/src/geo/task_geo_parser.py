import itertools

from django.conf import settings

from data.models import GeoCity, GeoCountry, GeoLocation, GeoLocationMembership, Paper, VerificationState
from src.geo.geo_parser import GeoParser
from src.geo.country_data import CountryData
from tasks.definitions import register_task, Runnable

from termcolor import colored

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

    def update_counts(self):
        for location in itertools.chain(GeoCountry.objects.all(), GeoCity.objects.all()):
            location.count = location.papers.count()
            location.save()

    def run(self):
        n_locations = 0

        with GeoParser(log=self.log, db_path=f'{settings.RESOURCES_DIR}/geonames/geonames.sqlite3') as geo:
            updated = False
            for paper in Paper.objects.all():
                locations, ignored_entities = geo.parse(paper.title, merge=True)

                first = True
                for location, usage in locations:
                    word = usage['word'].strip()
                    if word in ('CT', 'MS'):
                        # Ignore location CT and MS, which refers in almost all cases to
                        # "computed tomography" and "MS" in medical context rather than Connecticut/Mississippi.
                        continue

                    country_data = CountryData.get(location.country_code)
                    db_country, country_created = GeoCountry.objects.get_or_create(
                        name=country_data['name'],
                        alias=country_data['alias'],
                        alpha_2=location.country_code,
                        latitude=country_data['lat'],
                        longitude=country_data['lon'],
                    )

                    if location.feature_label.startswith('A.PCL'):
                        db_location = db_country
                        created = country_created
                    else:
                        try:
                            db_location = GeoLocation.objects.get(name=location.name)
                            created = False
                        except GeoLocation.DoesNotExist:
                            db_location = GeoCity.objects.create(
                                    name=location.name,
                                    country=db_country,
                                    latitude=location.latitude,
                                    longitude=location.longitude,
                            )
                            created = True

                    if db_location not in paper.locations.all():
                        membership = GeoLocationMembership(
                            paper=paper,
                            location=db_location,
                            state=VerificationState.AUTOMATICALLY_ACCEPTED,
                        )
                        membership.save()
                        n_locations += 1
                        updated = True
                        added = True
                    else:
                        added = False

                    if first and (len(ignored_entities) > 0 or added or created):
                        first = False
                        self.log(paper.title)

                        for ent in ignored_entities:
                            self.log("\t[{:7}] {:30}".format(colored('ignored', 'red'), ent))

                    if created or added:
                        status = 'created' if created else 'added'
                        self.log(
                            "\t[{:16}] {:20} -> {}".format(colored(status, 'green'), word, db_location.name)
                        )

                if updated:
                    paper.save()
                    updated = False

        self.log(f"Found {n_locations} locations")
        self.log(f"Update counts")
        self.update_counts()