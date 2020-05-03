import datetime
from tasks.models import Task
from django.utils.timezone import datetime
from django.conf import settings

AVAILABLE_TASKS = dict()


# noinspection PyPep8Naming
def register_task(cls):
    global AVAILABLE_TASKS
    AVAILABLE_TASKS[cls.task_name()] = cls
    return cls


class Runnable:
    def __init__(self, task: Task, *args, **kwargs):
        self._task = task

        self.__message_buffer = []
        self.__log_updated_at = datetime.now()

    def log(self, *args, flush=False):
        message = '[' + datetime.now().strftime("%d.%b %Y %H:%M:%S") + ']\t'
        message += " ".join([str(x) for x in list(args)])
        self.__message_buffer.append(message)

        if settings.DEBUG:
            print(message)

        if flush or (
                datetime.now() - self.__log_updated_at).total_seconds() / 60 > settings.TASK_LOGGING_DB_FLUSH_MINUTES:
            self.flush()

    def run(self):
        pass

    def flush(self):
        if len(self.__message_buffer) > 0:
            self._task.log += "\n".join(self.__message_buffer) + "\n"
            self._task.save()
            self.__log_updated_at = datetime.now()

    @staticmethod
    def task_name():
        raise NotImplementedError("Task has no name")

    @staticmethod
    def description():
        return 'Description'
