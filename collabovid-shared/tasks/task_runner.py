from tasks.models import Task
import traceback
import django.utils.timezone as timezone
from threading import Thread


class TaskRunner:

    @staticmethod
    def run_task(cls, *args, **kwargs):
        task = Task(name=cls.task_name(),
                    started_at=timezone.now(),
                    status=Task.STATUS_PENDING,
                    started_by=kwargs['started_by'])
        task.save()
        runnable = cls(*args, **dict(kwargs, task=task))

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
        runnable.flush()
        task.save()
        print("saved", task)

    @staticmethod
    def run_task_async(cls, *args, **kwargs):
        thread = Thread(target=TaskRunner.run_task, args=args, kwargs=dict(kwargs, cls=cls))
        thread.start()


class CommandLineTaskRunner:

    @staticmethod
    def run_task():
        import argparse
        import json

        from tasks.definitions import SERVICE_TASKS, SERVICE_TASK_DEFINITIONS, PrimitivesHelper

        parser = argparse.ArgumentParser()
        parser.add_argument('-u', '--user', default='default')
        parser.add_argument('-l', '--list', action='store_true')
        subparsers = parser.add_subparsers(help='Different tasks', dest='task')

        for task_name, definition in SERVICE_TASK_DEFINITIONS.items():

            task_parser = subparsers.add_parser(task_name)

            for parameter in definition['parameters']:
                if parameter['is_primitive']:
                    if parameter['type'] == 'bool':
                        task_parser.add_argument('--' + parameter['name'],
                                                 action='store_true',
                                                 default=False)
                    else:
                        task_parser.add_argument('--' + parameter['name'],
                                                 type=PrimitivesHelper.from_string(parameter['type']),
                                                 required=parameter['required'],
                                                 default=parameter['default'])

        args = parser.parse_args()

        if args.list:
            with open('tasks.json', 'w') as f:
                json.dump(SERVICE_TASK_DEFINITIONS, f)
        else:

            task_name = args.task

            if task_name not in SERVICE_TASKS:
                print('Error Unknown Task: ', args.task)
                exit(1)

            args_dict = vars(args)
            task_arguments = dict()

            definition = SERVICE_TASK_DEFINITIONS[task_name]

            for parameter in definition['parameters']:
                if parameter['name'] in args_dict:
                    task_arguments[parameter['name']] = args_dict[parameter['name']]

            task_cls = SERVICE_TASKS[task_name]
            TaskRunner.run_task(task_cls, started_by=args.user, **task_arguments)
