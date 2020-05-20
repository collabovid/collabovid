from .command import Command


class RegisterCommand(Command):
    def run(self, args):
        self.run_shell_command(
            f"eksctl create iamidentitymapping --cluster {args.cluster} --arn {args.arn} "
            f"--group system:masters --username {args.username} --region {args.region}")

    def add_arguments(self, parser):
        super().add_arguments(parser)
        parser.add_argument('--arn', type=str)
        parser.add_argument('--cluster', type=str)
        parser.add_argument('--username', type=str)
        parser.add_argument('--region', type=str)

    def help(self):
        return "Adds user to the cluster"

    def name(self):
        return "register"
