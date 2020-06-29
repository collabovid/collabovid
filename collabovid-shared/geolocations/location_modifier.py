from django.conf import settings
from django.db import IntegrityError

from data.models import GeoLocation, GeoLocationMembership, GeoNameResolution
from geolocations.geoname_db import GeonamesDB, Location


class LocationModifier:
    @staticmethod
    def delete_and_ignore_location(location):
        """Removes location and all associated location memberships and add all membership words to ignore list."""
        memberships = GeoLocationMembership.objects.filter(location=location)

        for membership in memberships:
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
        try:
            new_location = GeoLocation.objects.get(geonames_id=new_geonames_id)
        except GeoLocation.DoesNotExist:
            with GeonamesDB(f'{settings.RESOURCES_DIR}/{settings.GEONAMES_DB_PATH}') as geonames_db:
                geonames_object = geonames_db.locations.filter(Location.id == new_geonames_id).first()
            new_location = GeoLocation.get_or_create_from_geonames_object(geonames_object)

        for membership in GeoLocationMembership.objects.filter(location=location):
            membership.location = new_location
            membership.save()
            try:
                GeoNameResolution.objects.create(source_name=membership.word.lower(), target_geonames_id=new_geonames_id)
            except IntegrityError:
                pass
        location.delete()
