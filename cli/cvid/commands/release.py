from .command import Command
import json


class ReleaseCommand(Command):
    def run(self, args):
        if not args.no_build:
            self.run_shell_command('cvid build --all')
        if not args.no_push:
            self.run_shell_command('cvid push --all')

        kubectl = self.current_env_config()['kubectl']
        job_name = 'check-migrations'
        self.run_shell_command(f"cvid jobs run {job_name}")
        self.run_shell_command(f"{kubectl} wait --for=condition=complete job/{job_name} --timeout=120s")
        result = self.run_shell_command(f"{kubectl} logs  --selector=job-name={job_name}", collect_output=True)
        output = result.stdout.decode('utf-8').strip()
        migration_state = json.loads(output)
        if migration_state['is_synchronized']:
            print('No migrations are pending. Deploying..')
        else:
            print('There are the following migrations pending')
            print('\n'.join(migration_state['pending_migrations']))
            exit(1)

        self.run_shell_command('cvid cluster apply --all')
        if args.restart:
            self.run_shell_command('cvid cluster restart --all')

    def add_arguments(self, parser):
        parser.add_argument('--restart', action='store_true')
        parser.add_argument('--no-build', action='store_true')
        parser.add_argument('--no-push', action='store_true')

    def help(self):
        return "Full build, push and cluster update"

    def name(self):
        return "release"
