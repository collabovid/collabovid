from cvid.commands.command import Command


class CommandWithServices(Command):
    def run(self, args):
        if args.all:
            args.services = self.config['services'].items()
            print("No Service specified: Running for all..")
        else:
            args.services = [(service, self.config['services'][service]) for service in args.services]

    def add_arguments(self, parser):
        group = parser.add_mutually_exclusive_group(required=True)
        group.add_argument('--all', action='store_true')
        group.add_argument('-s', '--services', nargs='*', choices=self.config['services'].keys(),
                           help="Specify multiple values of {} or use all".format(self.config['services'].keys()))
