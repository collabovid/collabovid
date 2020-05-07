from .command import Command


class AWSRegistryLoginCommand(Command):
    def run(self, args):
        region = args.region
        registry = self.current_env_config()['registry']
        self.run_shell_command(
            "aws ecr get-login-password --region {} | docker login --username AWS --password-stdin {}".format(region, registry))

    def add_arguments(self, parser):
        parser.add_argument('-r', '--region', choices=['us-east-1', 'eu-central-1'])

    def help(self):
        return "Login the docker client into the registry"

    def name(self):
        return "aws-registry-login"
