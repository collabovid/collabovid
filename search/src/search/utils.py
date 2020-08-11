from django.conf import settings
import time


class TimerUtilities:
    """
    This class provides functions that give insights on the performance of certain
    search methods.
    """
    @staticmethod
    def time_function(function, *args, **kwargs):
        """
        Times a given function in DEBUG mode and prints the result to the console.
        :param function: The function
        :param args: The arguments that should be passed to the function.
        :param kwargs: The arguments that should be passed to the function.
        :return: The function result.
        """
        if settings.DEBUG:
            start_time = time.monotonic()
            result = function(*args, **kwargs)
            print(function.__class__.__name__, function.__name__, 'took', time.monotonic() - start_time)
            return result
        else:
            return function(*args, **kwargs)