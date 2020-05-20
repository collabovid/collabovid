import subprocess
from os.path import join, exists
import os
from subprocess import PIPE


class Command:
    def __init__(self, config, user_config):
        self.config = config
        self.user_config = user_config

    def run(self, args):
        raise NotImplementedError()

    def add_arguments(self, parser):
        pass

    def name(self):
        raise NotImplementedError()

    def help(self):
        return ""

    def print_info(self, info):
        bold = '\033[1m'
        ansi_reset = "\u001B[0m"
        print(bold + info + ansi_reset)

    def current_env(self):
        return self.config['env']

    def current_env_config(self):
        return self.config['envs'][self.current_env()]

    def resource_exists(self, resource, name):
        result = self.run_shell_command(
            f'{self.kubectl} get {resource} --field-selector=metadata.name={name} -o jsonpath={{.items}}',
            collect_output=True, print_command=False)
        return result.stdout.decode('utf8') != '[]'

    @property
    def kubectl(self):
        return self.current_env_config()['kubectl']

    def run_shell_command(self, cmd, cwd=None, collect_output=False, print_command=True,
                          quiet=False, exit_on_fail=True):
        if print_command:
            self.print_info("\033[1;36m" + f"Running: {cmd}" + "\u001B[0m")
        try:
            if collect_output:
                result = subprocess.run(cmd, shell=True, cwd=cwd, stdout=PIPE, check=exit_on_fail)
                stdout = result.stdout.decode('utf8')
                if not quiet:
                    print(stdout.rstrip())
                return result
            else:
                subprocess.run(cmd, shell=True, cwd=cwd, check=exit_on_fail)
        except subprocess.CalledProcessError as e:
            print('\033[91m' + f"Aborting. {str(e)}" + "\u001B[0m")
            exit(42)

    @property
    def services(self):
        return self.config['services']

    def call_command(self, cmd, *args, **kwargs):
        return self.run_shell_command(f'cvid {cmd}', *args, **kwargs)

    def generate_tag(self):
        result = subprocess.run("echo $(date +%Y%m%d).$(git log -1 --pretty=%h)", shell=True, stdout=PIPE)
        tag = result.stdout.decode('utf-8').strip()
        return tag

    def build_kubernetes_config(self, image_tag=None, customize_callback=None, quiet=True):
        env = self.current_env()
        kubernetes_dir = join(os.getcwd(), 'k8s')
        if not exists(kubernetes_dir):
            print('Did not find k8s directory in cwd')
            exit(1)
        temp_dir = join(kubernetes_dir, 'tmp')
        kubernetes_env_dir = join(kubernetes_dir, 'overlays', env)
        self.run_shell_command('mkdir -p {} && cp -r {} {}'.format(temp_dir, kubernetes_env_dir, temp_dir), quiet=quiet)
        for repo, config in self.config['services'].items():
            if image_tag is None:
                image_tag = self.generate_tag()
            registry = self.current_env_config()['registry']
            if len(registry) > 0:
                registry += '/'
            self.run_shell_command(
                '(cd {} && kustomize edit set image {}={}{}:{})'.format(join(temp_dir, env), repo, registry, repo,
                                                                        image_tag), quiet=quiet)

        options_dir = join(kubernetes_dir, 'options')
        for option in self.current_env_config()['optionFiles']:
            option_file_path = join(options_dir, option)
            if not exists(option_file_path):
                print("Unknown optionFiles item specified in config: {}".format(option))
                exit(2)
            option_name = option.replace('/', '-')
            self.run_shell_command("cp {} {}".format(option_file_path, join(temp_dir, env, 'option-' + option_name)),
                                   quiet=quiet)
            self.run_shell_command(
                "(cd {} && kustomize edit add patch {})".format(join(temp_dir, env), ('option-' + option_name)),
                quiet=quiet)

        # allow caller to add further customization
        if customize_callback is not None:
            customize_callback(join(temp_dir, env))

        self.run_shell_command('{} {} {}'.format(join(kubernetes_dir, 'build.sh'), join(temp_dir, env), env),
                               quiet=quiet)
        self.run_shell_command('rm -rf {}'.format(temp_dir), quiet=quiet)
