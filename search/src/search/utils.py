from django.conf import settings
import time


class TimerUtilities:

    @staticmethod
    def time_function(function, *args, **kwargs):
        if settings.DEBUG:
            start_time = time.monotonic()
            result = function(*args, **kwargs)
            print(function.__class__.__name__, function.__name__, 'took', time.monotonic() - start_time)
            return result
        else:
            return function(*args, **kwargs)