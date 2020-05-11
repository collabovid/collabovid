from .command import Command, CommandWithServices


class PushCommand(CommandWithServices):
    def run(self, args):
        super().run(args)
        for service, config in args.services:
            tag = self.generate_tag()
            self.print_info("Tagging Image: {}:{}".format(service, tag))
            registry = self.current_env_config()['registry']
            self.run_shell_command("docker tag {}:{} {}/{}:{}".format(service, tag, registry, service, tag))
            self.print_info("Pushing image: {}:{}".format(service, tag))
            self.run_shell_command("docker push {}/{}:{}".format(registry, service, tag))

    def add_arguments(self, parser):
        super().add_arguments(parser)

    def help(self):
        return "Pushes the image of a service to the registry defined by the current environment"

    def name(self):
        return "push"
