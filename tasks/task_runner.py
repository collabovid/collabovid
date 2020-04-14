from tasks.models import Task
import traceback
import django.utils.timezone as timezone
from threading import Thread

class TaskRunner:

    @staticmethod
    def run_task(cls, *args, **kwargs):
        task = Task(name=cls.task_name(), started_at=timezone.now(), status=Task.STATUS_PENDING)
        task.save()
        runnable = cls(*args, **dict(kwargs, log_file=task.log_file))

        try:
            runnable.run()
        except (KeyboardInterrupt, SystemExit):
            runnable.log("Task was aborted by system exit or keyboard interrupt")
            task.status = Task.STATUS_ERROR
            raise
        except Exception as e:
            runnable.log("Error during execution:", str(e))
            runnable.log(traceback.format_exc())
            task.status = Task.STATUS_ERROR
        else:
            runnable.log("Finished", cls.task_name(), "without exceptions")
            task.status = Task.STATUS_FINISHED

        task.ended_at = timezone.now()
        task.save()

    @staticmethod
    def run_task_async(cls, *args, **kwargs):
        thread = Thread(target=TaskRunner.run_task, args=args, kwargs=dict(kwargs, cls=cls))
        thread.start()


