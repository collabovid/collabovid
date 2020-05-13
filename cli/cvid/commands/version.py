from .command import Command


class VersionCommand(Command):
    def run(self, args):
        output = self.run_with_output(f"{self.kubectl} get deployments -o jsonpath='{{..image}}'")
        output += ' ' + self.run_with_output(f"{self.kubectl} get daemonsets -o jsonpath='{{..image}}'")
        version = None
        for registry_image in output.split(' '):
            image = registry_image.split('/')[-1]
            tokens = image.split(':')
            if len(tokens) != 2:
                continue
            service, tag = tokens
            if service in list(self.services.keys()):
                if version is None:
                    version = tag
                elif version != tag:
                    print(f'Two different versions running in cluster: {version} and {tag}')
                    exit(1)
        print(version)

    def run_with_output(self, cmd):
        output = self.run_shell_command(cmd, collect_output=True,print_command=False)
        output = output.stdout.decode('utf8').strip()
        return output

    def add_arguments(self, parser):
        pass

    def help(self):
        return "Retrieves the currently running version in the cluster"

    def name(self):
        return "version"
