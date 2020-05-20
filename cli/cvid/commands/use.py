from .command import Command


class UseCommand(Command):
    def run(self, args):
        self.user_config['env'] = args.env
        self.print_info("Using environment: {}".format(args.env))

    def add_arguments(self, parser):
        parser.add_argument('env', choices=self.config['envs'].keys())

    def help(self):
        return "Specify which environment to use. Options are: {}".format(self.config['envs'].keys())

    def name(self):
        return "use"
