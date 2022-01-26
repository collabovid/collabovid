from .command import Command
import json
import datetime
import os
from os.path import join


class ReleaseCommand(Command):
    def run(self, args):
        release_dict = {}

        result = self.call_command('version', collect_output=True, exit_on_fail=True, quiet=True)
        version = result.stdout.decode('utf8').strip()

        # saving previous running version
        release_dict['old_version'] = version
        print(f'Current version on the cluster: {version}')

        # Building and pushing
        if not args.no_build:
            self.call_command('build --all')
        if not args.no_push:
            self.call_command('push --all')

        # Build config ones and then specify --no-config build for the next calls
        self.build_kubernetes_config()

        # Apply all secrets (jobs need the secrets)
        self.call_command('cluster apply -r secret --all --no-config-build')

        # In order to check if migrations are pending we have to communicate with the database
        if self.current_env() in ['dev', 'single-node']:
            # Start the postgres deployment if in dev mode
            self.call_command('cluster apply -r deployment -n postgres --no-config-build')

        # The start the service, in prod we only need the service
        self.call_command('cluster apply -r service -n postgres --no-config-build')

        # Checking for migrations
        job_name = 'check-migrations'
        success, version = self.run_job_to_completion(job_name, timeout=args.timeout)
        if not success:
            print(f"{job_name} did not complete")
            exit(1)
        print(version)
        migration_state = json.loads(version)

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
            success, version = self.run_job_to_completion('migrate', timeout=args.timeout)
            if success:
                self.print_info('Migration completed successfully')
                print(version)
            else:
                self.print_info('Migration failed')
                exit(3)

        release_dict['new_version'] = self.generate_tag()

        # Applying to cluster
        self.call_command('cluster apply --all --no-config-build')
        if args.restart:
            self.call_command('cluster restart --all --no-config-build')

        if not args.no_cronjob:
            for cronjob_name in ['scrape-cron', 'altmetric-update-cron']:
                if self.resource_exists('cronjob', cronjob_name):
                    self.print_info(f"Applying {cronjob_name}")
                    self.call_command(f'cronjobs apply -n {cronjob_name}')
                else:
                    self.print_info(f"Not applying {cronjob_name} because it is currently not in the cluster applied")
        else:
            self.print_info("Not applying scrape cronjob")

        self.save_release_file(release_dict)

    def create_db_snapshot(self):
        pass

    def run_job_to_completion(self, job_name, timeout):
        self.run_shell_command(f"cvid jobs run -n {job_name} --no-config-build")
        result = self.run_shell_command(
            f"{self.kubectl} wait --for=condition=complete job/{job_name} --timeout={timeout}s",
            collect_output=True, exit_on_fail=False)
        if result.returncode != 0:
            # job was not completed
            return False, None
        else:
            result = self.run_shell_command(f"{self.kubectl} logs --tail=-1 --selector=job-name={job_name}",
                                            collect_output=True, quiet=True)
            output = result.stdout.decode('utf-8').strip()
            return True, output

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
        parser.add_argument('--no-cronjob', action='store_true')
        parser.add_argument('-y', action='store_true')
        parser.add_argument('-t', '--timeout', type=int, default=120)

    def help(self):
        return "Full build, push and cluster update"

    def name(self):
        return "release"
