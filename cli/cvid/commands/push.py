from .command import Command, CommandWithRepositories


class PushCommand(CommandWithRepositories):
    def run(self, args):
        super().run(args)
        for repository, config in args.repositories:
            tag = config['version']
            self.print_info("Tagging Image: {}:{}".format(repository, tag))
            registry = self.current_env_config()['registry']
            self.run_shell_command("docker tag {}:{} {}/{}:{}".format(repository, tag, registry, repository, tag))
            self.print_info("Pushing image: {}:{}".format(repository, tag))
            self.run_shell_command("docker push {}/{}:{}".format(registry, repository, tag))

    def add_arguments(self, parser):
        super().add_arguments(parser)

    def help(self):
        return "Pushes an repository to the registry defined by the current environment"

    def name(self):
        return "push"
