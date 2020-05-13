from .command import Command
import json
import datetime
import os
from os.path import join


class ReleaseCommand(Command):
    def run(self, args):
        release_dict = {}

        result = self.call_command('version', collect_output=True)
        output = result.stdout.decode('utf8').strip()
        if result.returncode != 0:
            print('Getting version failed: ' + output)
            exit(4)

        # saving previous running version
        release_dict['old_version'] = output
        print(f'Current version on the cluster: {output}')

        # Building and pushing
        if not args.no_build:
            self.call_command('build --all')
        if not args.no_push:
            self.call_command('push --all')

        # Build config ones and then specify --no-config build for the next calls
        self.build_kubernetes_config()

        # Checking for migrations
        job_name = 'check-migrations'
        success, output = self.run_job_to_completion(job_name, timeout=args.timeout)
        if not success:
            print(f"{job_name} did not complete")
            exit(1)

        migration_state = json.loads(output)

        # Check if migrations have to be applied
        if migration_state['is_synchronized']:
            self.print_info('No migrations are pending. Deploying..')
            release_dict['rollback_points'] = []
        else:
            self.print_info('There are the following migrations pending')
            print('\n'.join(migration_state['pending_migrations']))
            release_dict['rollback_points'] = migration_state['rollback_points']
            if not args.y:
                answer = self.ask_for_confirmation('Do you want to continue?')
                if not answer:
                    print('Aborting..')
                    exit(2)
            if not args.no_db_snapshot:
                self.print_info('Creating db snapshot')
                self.create_db_snapshot()
            self.print_info('Migrating')
            success, output = self.run_job_to_completion('migrate', timeout=args.timeout)
            if success:
                self.print_info('Migration completed successfully')
                print(output)
            else:
                self.print_info('Migration failed')
                exit(3)

        release_dict['new_version'] = self.generate_tag()

        # Applying to cluster
        self.call_command('cluster apply --all')
        if args.restart:
            self.call_command('cluster restart --all')

        self.save_release_file(release_dict)

    def create_db_snapshot(self):
        pass

    def run_job_to_completion(self, job_name, timeout):
        kubectl = self.current_env_config()['kubectl']
        self.run_shell_command(f"cvid jobs run {job_name} --no-config-build")
        result = self.run_shell_command(
            f"{kubectl} wait --for=condition=complete job/{job_name} --timeout={timeout}s", collect_output=True)
        if result.returncode != 0:
            # job was not completed
            return False, None
        else:
            result = self.run_shell_command(f"{kubectl} logs --tail=-1 --selector=job-name={job_name}",
                                            collect_output=True)
            output = result.stdout.decode('utf-8').strip()
            return True, output

    def ask_for_confirmation(self, question):
        print(f"{question} (y/n)")
        answer = input()
        while answer not in ['y', 'n']:
            print('Please specify \'y\' or \'n\'')
            answer = input()
        return answer == 'y'

    def save_release_file(self, release_dict):
        deploy_time = datetime.datetime.utcnow().replace(microsecond=0).strftime('%Y-%m-%d-%H-%M-%S')
        release_dir = join(os.getcwd(), 'release')
        os.makedirs(release_dir, exist_ok=True)
        with open(join(release_dir, f'{deploy_time}.json'), 'w+') as f:
            json.dump(release_dict, f, indent=4)

    def add_arguments(self, parser):
        parser.add_argument('--restart', action='store_true')
        parser.add_argument('--no-build', action='store_true')
        parser.add_argument('--no-push', action='store_true')
        parser.add_argument('--no-db-snapshot', action='store_true')
        parser.add_argument('-y', action='store_true')
        parser.add_argument('-t', '--timeout', type=int, default=120)

    def help(self):
        return "Full build, push and cluster update"

    def name(self):
        return "release"
