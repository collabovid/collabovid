from cvid.commands.abstract.with_services import CommandWithServices


class PushCommand(CommandWithServices):
    def run(self, args):
        super().run(args)
        for service, config in args.services:
            tag = self.generate_tag()
            registry = self.current_env_config()['registry']
            local_image = f"{service}:{tag}"
            registry_image = f"{registry}/{local_image}"
            self.run_shell_command(f"docker tag {local_image} {registry_image}")
            self.print_info(f"Pushing image: {local_image}")
            self.run_shell_command(f"docker push {registry_image}")
            self.run_shell_command(f"docker rmi {registry_image}")

    def add_arguments(self, parser):
        super().add_arguments(parser)

    def help(self):
        return "Pushes the image of a service to the registry defined by the current environment"

    def name(self):
        return "push"
