from .command import Command
import json
import os

from cvid.utils.dict_utils import DictUtils


class CollectTasksCommand(Command):
    """
    Collects the tasks from all services and saves them into the collabovid-shared project.
    """

    SERVICES_WITH_TASKS = ['scrape', 'search']

    def run(self, args):

        all_tasks = {
            service: [] for service in CollectTasksCommand.SERVICES_WITH_TASKS
        }

        for service in CollectTasksCommand.SERVICES_WITH_TASKS:

            service_path = os.path.join(os.getcwd(), service)

            print(self.run_shell_command("python run_task.py --list", service_path, collect_output=True))

            tasks_json_path = os.path.join(service_path, 'tasks.json')

            with open(tasks_json_path, 'r') as f:
                tasks = json.load(f)

                all_tasks[service] = tasks

            print("Cleaning up", tasks_json_path)
            os.remove(tasks_json_path)

        tasks_output_path = os.path.join(os.getcwd(), "collabovid-shared/tasks/resources/tasks.json")
        with open(tasks_output_path, 'w') as f:
            json.dump(all_tasks, f, indent=4)

        print("Successfully dumped all tasks to", tasks_output_path)

    def add_arguments(self, parser):
        pass

    def help(self):
        return "Collects all tasks from " + ",".join(CollectTasksCommand.SERVICES_WITH_TASKS)

    def name(self):
        return "collect-tasks"
