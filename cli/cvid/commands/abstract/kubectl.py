from os.path import join
from cvid.commands.command import Command


class KubectlCommand(Command):
    def run(self, args):
        if not args.no_config_build:
            print('Building')
            self.build_kubernetes_config(image_tag=args.tag)

    def add_arguments(self, parser):
        parser.add_argument('-t', '--tag', default=None,
                            help="Specifies the image tag that should be used when building the cluster config")
        parser.add_argument('--no-config-build', action='store_true')

    @property
    def k8s_dist_path(self):
        return join('k8s', 'dist')

    @property
    def k8s_dist_env_path(self):
        return join(self.k8s_dist_path, self.current_env())
