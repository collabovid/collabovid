import datetime
import inspect
import re

from django.db.models import QuerySet

from tasks.models import Task
from django.utils.timezone import datetime
from django.conf import settings
from tasks.colors import LogColor
from math import ceil

"""
Service tasks are tasks that are unique to the service you are running, i.e. they do not include tasks that
are defined by other services
"""
SERVICE_TASKS = dict()
SERVICE_TASK_DEFINITIONS = dict()


class PrimitivesHelper:
    """
    Helps to convert primitives to a readable string format for the tasks definitions dict.
    """
    PRIMITIVES = [int, str, bool]
    PRIMITIVES_STRINGS = ['int', 'str', 'bool']

    @staticmethod
    def is_primitive(data_type):
        return data_type in PrimitivesHelper.PRIMITIVES

    @staticmethod
    def to_string(data_type):
        return PrimitivesHelper.PRIMITIVES_STRINGS[PrimitivesHelper.PRIMITIVES.index(data_type)]

    @staticmethod
    def from_string(data_type):
        return PrimitivesHelper.PRIMITIVES[PrimitivesHelper.PRIMITIVES_STRINGS.index(data_type)]

    @staticmethod
    def convert(data_type, data: str):
        return PrimitivesHelper.PRIMITIVES[PrimitivesHelper.PRIMITIVES_STRINGS.index(data_type)](data)


# noinspection PyPep8Naming
def register_task(cls):
    """
    This annotation registers the given task class.
    :param cls: Automatically passed when annotating in front of a class definition
    :return: Returns the class as usual for Python annotations.
    """
    global SERVICE_TASKS

    SERVICE_TASKS[cls.task_name()] = cls
    SERVICE_TASK_DEFINITIONS[cls.task_name()] = dict()
    SERVICE_TASK_DEFINITIONS[cls.task_name()]['name'] = cls.display_name()
    SERVICE_TASK_DEFINITIONS[cls.task_name()]['description'] = cls.description()
    SERVICE_TASK_DEFINITIONS[cls.task_name()]['parameters'] = list()

    for param in inspect.signature(cls.__init__).parameters.values():
        if param.name not in ['self', 'args', 'kwargs']:
            SERVICE_TASK_DEFINITIONS[cls.task_name()]['parameters'].append({
                'name': param.name,
                'required': param.default == inspect.Parameter.empty,
                'type':
                    str(param.annotation.__name__) if not PrimitivesHelper.is_primitive(
                        param.annotation) else  # class name
                    None if param.annotation == inspect.Parameter.empty else  # No annotation
                    PrimitivesHelper.to_string(param.annotation),  # Annotation is a primitive
                'default': None if param.default == inspect.Parameter.empty else param.default,
                'is_primitive': True if PrimitivesHelper.is_primitive(param.annotation) else False
            })
    return cls


class Runnable:
    """
    Defines an interface for runnable tasks. A runnable is assigned to a database task and has certain attributes
    such as a task name or a description.
    Furthermore this class implements some logging helper function that should be used by any task of the Collabovid
    project.
    """

    def __init__(self, task: Task, *args, **kwargs):
        self._task = task

        self.__message_buffer = []
        self.__log_updated_at = datetime.now()

    def _progress_iterator(self, iterator, length=None, proportion: float = 1.0, step_size: int = 1):
        """
        Yields the given iterator while updating the task progress automatically.
        :param iterator: The iterator or QuerySet or an int that should be set as the progress
        :param length: The length of the iterator. If nothing is provided len() will be used which might be inefficient.
        :param proportion: The proportion of progress this iterator should cover.
        :param step_size: The step size (in percent) in which the task progress should be updated. For large iterator
                this value should be lowered while for small iterators a large step size is sufficient. Min value is 1.
        :return: Yields the iterators objects.
        """

        assert 0 <= proportion <= 1 <= step_size

        if not length:
            if isinstance(iterator, QuerySet):
                length = iterator.count()
            else:
                length = len(iterator)

        if length < 1:
            return

        progress_to_cover = int(round(100 * proportion))
        iterations_per_percent = int(ceil(progress_to_cover/length))
        buffered_progress = 0

        for i, obj in enumerate(iterator, 1):
            if i % iterations_per_percent == 0:
                #  Progress increased by 1
                buffered_progress += 1
                if buffered_progress == step_size:
                    #  Progress update in database, never increase progress to > 100
                    self._task.progress = min(self._task.progress + buffered_progress, 100)
                    self._task.save()
                    buffered_progress = 0

            yield obj

    def progress(self, progress_or_iterator, length=None, proportion: float = 1.0, step_size: int = 1):
        """
        Yields the given iterator while updating the task progress automatically or applies the given progress.
        :param progress_or_iterator: The progress, iterator or QuerySet or an int that should be set as the progress.
        :param length: The length of the iterator. If nothing is provided len() will be used which might be inefficient.
        :param proportion: The proportion of progress this iterator should cover.
        :param step_size: The step size (in percent) in which the task progress should be updated. For large iterator
                this value should be lowered while for small iterators a large step size is sufficient. Min value is 1.
        :return: Yields the iterators objects.
        """
        if isinstance(progress_or_iterator, int):
            self._task.progress = min(progress_or_iterator, 100)
            self._task.save()
            return None
        else:
            return self._progress_iterator(progress_or_iterator, length=length, proportion=proportion,
                                           step_size=step_size)

    def log(self, *args, flush=False) -> None:
        """
        Logs given messages to the database. The log will only be flushed after a certain time period or when
        the task has finished. This includes flushing when a non-critical exception occurs.
        :param args: The messages that should be written into the log.
        :param flush: Determines weather a flush should be forced now or after the time period.
        :return: None
        """

        datetime_prefix = '[' + datetime.now().strftime("%d.%b %Y %H:%M:%S") + ']\t'

        log_message = datetime_prefix + " ".join(
            [message.database_message if isinstance(message, LogColor) else str(message) for message in list(args)])

        self.__message_buffer.append(log_message)

        if settings.DEBUG:
            terminal_message = datetime_prefix + " ".join(
                [message.terminal_message if isinstance(message, LogColor) else str(message) for message in list(args)])

            print(terminal_message, flush=True)

        if flush or (
                datetime.now() - self.__log_updated_at).total_seconds() > settings.TASK_LOGGING_DB_FLUSH_SECONDS:
            self.flush()

    def run(self):
        pass

    def flush(self):
        if len(self.__message_buffer) > 0:
            self._task.log += "\n".join(self.__message_buffer) + "\n"
            self._task.save()
            self.__log_updated_at = datetime.now()
            self.__message_buffer.clear()

    @staticmethod
    def task_name():
        raise NotImplementedError("Task has no name")

    @classmethod
    def display_name(cls):
        return cls.task_name().replace('-', ' ').title()

    @staticmethod
    def description():
        return 'No description provided.'
