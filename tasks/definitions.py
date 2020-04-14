import pathlib
from django.conf import settings
import datetime

AVAILABLE_TASKS = dict()


# noinspection PyPep8Naming
def register_task(cls):
    global AVAILABLE_TASKS
    AVAILABLE_TASKS[cls.task_name()] = cls
    return cls


class Runnable:
    def __init__(self, log_file, *args, **kwargs):
        self._log_file = log_file

        path = pathlib.Path(self._log_file)
        path.parent.mkdir(parents=True, exist_ok=True)

        self._file_handler = open(self._log_file, 'w')

    def log(self, *args):
        message = '[' + datetime.datetime.now().strftime("%d.%b %Y %H:%M:%S") + ']\t'
        message += " ".join([str(x) for x in list(args)])
        self._file_handler.write(message + "\n")
        self._file_handler.flush()

        if settings.DEBUG:
            print(message)

    def run(self):
        pass

    def __del__(self):
        if hasattr(self, "_file_handler") and self._file_handler:
            self._file_handler.close()

    @staticmethod
    def task_name():
        raise NotImplementedError("Task has no name")
