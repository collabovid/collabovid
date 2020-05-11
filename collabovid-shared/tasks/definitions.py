import datetime
import inspect
from tasks.models import Task
from django.utils.timezone import datetime
from django.conf import settings

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
                    str(param.annotation.__name__) if not PrimitivesHelper.is_primitive(param.annotation) else  # class name
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

    def log(self, *args, flush=False) -> None:
        """
        Logs given messages to the database. The log will only be flushed after a certain time period or when
        the task has finished. This includes flushing when a non-critical exception occurs.
        :param args: The messages that should be written into the log.
        :param flush: Determines weather a flush should be forced now or after the time period.
        :return: None
        """
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

    @classmethod
    def display_name(cls):
        return cls.task_name().replace('-', ' ').title()

    @staticmethod
    def description():
        return 'No description provided.'
