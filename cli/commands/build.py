from .command import Command, CommandWithRepositories


class BuildCommand(CommandWithRepositories):
    def run(self, args):
        super().run(args)
        for repository, config in args.repositories:
            self.print_info("Building repository: {}".format(repository))
            self.run_shell_command("DOCKER_BUILDKIT=1 docker build -t collabovid-base -f docker/collabovid-base.Dockerfile .")
            self.run_shell_command(
                "DOCKER_BUILDKIT=1 docker build -t {}:{} -f docker/{}.Dockerfile .".format(repository,
                                                                                           config['version'],
                                                                                           repository))

    def help(self):
        return "Specify which repository to use."

    def name(self):
        return "build"
