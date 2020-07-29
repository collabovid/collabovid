from django.conf import settings
from django.db import IntegrityError, transaction

from data.models import GeoLocation, GeoLocationMembership, GeoNameResolution, Paper, VerificationState
from geolocations.geoname_db import GeonamesDB, GeonamesDBError, Location


class LocationModifier:
    @staticmethod
    def delete_and_ignore_location(location):
        """Removes location and all associated location memberships and add all membership words to ignore list."""
        memberships = GeoLocationMembership.objects.filter(location=location)

        for membership in memberships:
            if membership.word:
                try:
                    resolution = GeoNameResolution.objects.get(source_name=membership.word.lower())
                    resolution.target_geonames_id = None
                    resolution.save()
                except GeoNameResolution.DoesNotExist:
                    GeoNameResolution.objects.create(source_name=membership.word.lower(), target_geonames_id=None)

        memberships.delete()
        location.delete()

    @staticmethod
    def change_location(location, new_geonames_id):
        """Maps an existing location to another location with the given Geonames ID."""
        try:
            new_location = GeoLocation.objects.get(geonames_id=new_geonames_id)
        except GeoLocation.DoesNotExist:
            with GeonamesDB(f'{settings.GEONAMES_DB_PATH}') as geonames_db:
                geonames_object = geonames_db.locations.filter(Location.id == new_geonames_id).first()
            if not geonames_object:
                raise GeonamesDBError(f"No Geonames object with ID {new_geonames_id}")
            new_location, _ = GeoLocation.get_or_create_from_geonames_object(geonames_object)

        for membership in GeoLocationMembership.objects.filter(location=location):
            GeoLocationMembership.objects.get_or_create(location=new_location, paper=membership.paper,
                                                        state=VerificationState.ACCEPTED)
            try:
                if membership.word:
                    GeoNameResolution.objects.create(source_name=membership.word.lower(),
                                                     target_geonames_id=new_geonames_id)
            except IntegrityError:
                pass
            membership.delete()
        if location.is_city and location.geocity.country.count == 0:
            location.geocity.country.delete()
        location.delete()
        return new_location

    @staticmethod
    def add_location(article, geonames_id):
        """Adds the given location to the given article and returns the possibly created location."""
        try:
            location = GeoLocation.objects.get(geonames_id=geonames_id)
        except GeoLocation.DoesNotExist:
            with GeonamesDB(f'{settings.GEONAMES_DB_PATH}') as geonames_db:
                geonames_object = geonames_db.locations.filter(Location.id == geonames_id).first()
            if not geonames_object:
                raise GeonamesDBError(f"No Geonames object with ID {geonames_id}")
            location, _ = GeoLocation.get_or_create_from_geonames_object(geonames_object)

        try:
            GeoLocationMembership.objects.create(location=location, paper=article,
                                                 word=None, state=VerificationState.ACCEPTED)
            article.location_modified = True
            article.save()
        except IntegrityError:
            pass
        return location

    @staticmethod
    def delete_location_membership(location_id, article_id):
        try:
            membership = GeoLocationMembership.objects.get(paper_id=article_id, location_id=location_id)
            with transaction.atomic():
                membership.delete()
                article = Paper.objects.get(doi=article_id)
                article.location_modified = True
                article.save()
                location = GeoLocation.objects.get(pk=location_id)
                if location.count == 0:
                    if location.is_city and location.geocity.country.count == 0:
                        location.geocity.country.delete()
                    location.delete()
            return True
        except GeoLocationMembership.DoesNotExist:
            return False
