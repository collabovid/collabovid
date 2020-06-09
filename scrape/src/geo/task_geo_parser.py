import itertools

from data.models import GeoAlias, GeoCity, GeoCountry, GeoLocation, GeoLocationMembership, Paper, VerificationState
from src.geo.geo_parser import GeoParser
from tasks.definitions import register_task, Runnable


@register_task
class GeoParserTask(Runnable):
    @staticmethod
    def task_name():
        return "parse-geo-locations"

    @staticmethod
    def description():
        return ""

    def __init__(self, *args, **kwargs):
        super(GeoParserTask, self).__init__(*args, **kwargs)
        self.force_recompute = False # TODO

    def update_counts(self):
        for location in itertools.chain(GeoCountry.objects.all(), GeoCity.objects.all()):
            location.count = location.papers.count()
            location.save()

    def run(self):
        if self.force_recompute:
            GeoLocationMembership.objects.exclude(state=VerificationState.ACCEPTED).delete()

        geo = GeoParser(log=self.log)

        n_locations = 0

        updated = False
        for paper in Paper.objects.all():
            locations = geo.parse(paper.title)

            first = True
            for location in locations:
                if not location["certain"]:
                    continue

                word = location["word"].strip()
                if word == "CT":
                    # Ignore location CT, which refers in almost all cases to "computed tomography" and not Connecticut.
                    continue

                created = False
                try:
                    db_location = GeoAlias.objects.get(name=word).geolocation
                except GeoAlias.DoesNotExist:
                    name = location["geo"]["place_name"]
                    try:
                        db_location = GeoLocation.objects.get(name=name)
                    except GeoLocation.DoesNotExist:
                        alpha_2 = location["is_country"] if location["is_country"] else location["geo"]["country_code2"]
                        country_data = GeoParser.get_country_data(alpha_2)

                        country, created = GeoCountry.objects.get_or_create(
                            name=country_data["name"],
                            alpha_2=alpha_2,
                            latitude=country_data["lat"],
                            longitude=country_data["lon"],
                        )

                        if location["is_country"] is None:
                            db_location = GeoCity.objects.create(
                                name=name,
                                country=country,
                                latitude=location["geo"]["lat"],
                                longitude=location["geo"]["lon"],
                            )
                            created = True
                        else:
                            db_location = country

                if db_location not in paper.locations.all():
                    membership = GeoLocationMembership(
                        paper=paper,
                        location=db_location,
                        state=VerificationState.AUTOMATICALLY_ACCEPTED,
                    )
                    membership.save()
                    n_locations += 1
                    updated = True

                if created:
                    status = 'created'
                elif updated:
                    status = 'add'
                else:
                    status = 'exist'

                if first:
                    first = False
                    self.log(paper.title)
                self.log("\t{:7} {:30}, {:50}".format(
                        status, word, db_location.name,
                ))
            if updated:
                paper.save()
                updated = False

        self.log(f"Found {n_locations} locations")
        self.log(f"Update counts")
        self.update_counts()
