from .command import Command


class ConfigureKubernetes(Command):

    def run(self, args):
        self.build_kubernetes_config(quiet=False)

    def help(self):
        return "Manage Kubernetes jobs"

    def name(self):
        return "configure-k8s"
