from .command import Command, CommandWithServices


class BuildCommand(CommandWithServices):
    def run(self, args):
        super().run(args)
        self.run_shell_command(
            "DOCKER_BUILDKIT=1 docker build -t collabovid-base -f docker/collabovid-base.Dockerfile .")

        self.run_shell_command("cd collabovid-shared; make")
        for service, config in args.services:
            self.print_info("Building service: {}".format(service))
            tag = self.generate_tag()
            image = f"{service}:{tag}"
            self.run_shell_command(f"DOCKER_BUILDKIT=1 docker build -t {image} -f docker/{service}.Dockerfile .")
            if args.delete_old:
                self.run_shell_command(
                    f"docker rmi $(docker image ls --filter reference=\"*/{service}\" --filter reference=\"{service}\" --format '{{{{.Repository}}}}:{{{{.Tag}}}}' | grep -v '...:{tag}')")

    def add_arguments(self, parser):
        super().add_arguments(parser)
        parser.add_argument('--delete-old', action='store_true')

    def help(self):
        return "Build a repository and tag it with the current version."

    def name(self):
        return "build"
