AVAILABLE_TASKS = dict()


# noinspection PyPep8Naming
class register_task:

    def __init__(self, name):
        self.name = name

    def __call__(self, cls, *args, **kwargs):
        global AVAILABLE_TASKS
        AVAILABLE_TASKS[self.name] = cls


class Runnable:
    def __init__(self, *args, **kwargs):
        pass

    def run(self):
        pass
