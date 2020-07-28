from django.utils.timezone import timedelta, datetime

class DateUtils:

    @staticmethod
    def all_sundays(year):
        d = datetime(year=year, month=1, day=1)  # January 1st
        d += timedelta(days=6 - d.weekday())  # First Sunday

        now = datetime.now()
        while d.year == year:

            if d.date() < now.date():
                yield d
                d += timedelta(days=7)
            else:
                yield now
                break
