import argparse
from cli.commands.use import UseCommand
from cli.commands.build import BuildCommand
from cli.commands.push import PushCommand
from cli.commands.cluster import ClusterCommand
from cli.commands.jobs import JobsCommand
from cli.commands.aws_registry_login import AWSRegistryLoginCommand
from cli.commands.cronjobs import CronJobsCommand
import json
from os.path import join, dirname, realpath
import copy


def merge_dicts(dict1, dict2):
    dict1 = copy.deepcopy(dict1)
    dict2 = copy.deepcopy(dict2)
    if not isinstance(dict1, dict) or not isinstance(dict2, dict):
        return dict2
    for k in dict2:
        if k in dict1:
            dict1[k] = merge_dicts(dict1[k], dict2[k])
        else:
            dict1[k] = dict2[k]
    return dict1


config_path = join(dirname((realpath(__file__))), 'config.json')
default_config_path = join(dirname((realpath(__file__))), 'defaults.json')

with open(config_path, 'r') as config, open(default_config_path, 'r') as default:
    defaults = json.load(default)
    config = json.load(config)
    user_config = config
    config = merge_dicts(defaults, config)
    for key in config['envs'].keys():
        config['envs'][key] = merge_dicts(config['env-defaults'], config['envs'][key])

args = {'config': config, 'user_config': user_config}
commands = [UseCommand(**args), BuildCommand(**args), PushCommand(**args),
            ClusterCommand(**args), JobsCommand(**args), AWSRegistryLoginCommand(**args),
            CronJobsCommand(**args)]

parser = argparse.ArgumentParser(prog='cvid')
subparsers = parser.add_subparsers()
for cmd in commands:
    subparser = subparsers.add_parser(name=cmd.name(), help=cmd.help())
    cmd.add_arguments(subparser)
    subparser.set_defaults(func=cmd.run)

args = parser.parse_args()
args.func(args)

with open(config_path, 'w') as f:
    json.dump(user_config, f, indent=4)
