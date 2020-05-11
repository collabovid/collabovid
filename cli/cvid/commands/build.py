from .command import Command, CommandWithServices


class BuildCommand(CommandWithServices):
    def run(self, args):
        super().run(args)
        for service, config in args.services:
            self.print_info("Building service: {}".format(service))
            self.run_shell_command(
                "DOCKER_BUILDKIT=1 docker build -t collabovid-base -f docker/collabovid-base.Dockerfile .")

            tag = self.generate_tag()
            self.run_shell_command(
                "DOCKER_BUILDKIT=1 docker build -t {}:{} -f docker/{}.Dockerfile .".format(service, tag, service))

    def help(self):
        return "Build a repository and tag it with the current version."

    def name(self):
        return "build"
