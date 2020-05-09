from dashboard.tasks.kube_job_utils import create_job_object, run_job, id_generator
import os
from os.path import join
from django.conf import settings
import subprocess


class TaskLauncher():
    def launch_task(self, name, config):
        raise NotImplementedError


secret_map = {
    'scrape': ['scrape', 'shared'],
    'web': ['web', 'shared'],
    'search': ['search', 'shared']
}


class KubeTaskLauncher(TaskLauncher):
    def launch_task(self, name, config):
        repository = config['repository']
        registry = os.getenv('REGISTRY', 'localhost:32000')
        if len(registry) > 0:
            registry += '/'
        version = '0.0.0'
        image = registry + repository + ':' + version
        job_object = create_job_object(name=name + '-' + id_generator(size=10), container_image=image,
                                       command=["bash", "-c"],
                                       args=["export PYTHONPATH=/app:$PYTHONPATH && python run_task.py " + name],
                                       secret_names=secret_map[repository])
        run_job(job_object)


class LocalTaskLauncher(TaskLauncher):
    def launch_task(self, name, config):
        repository = config['repository']
        script_path = join(settings.BASE_DIR, '..', repository, 'run_task.py')
        cmd = "python {} {} -u {}".format(script_path, name, 'web')
        subprocess.run(cmd, shell=True)
