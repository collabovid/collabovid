import os

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'web.settings_dev')
import django

django.setup()

from django.db.migrations.executor import MigrationExecutor
from django.db import connections, DEFAULT_DB_ALIAS
import json
from collections import defaultdict


def get_migration_info():
    database = DEFAULT_DB_ALIAS
    connection = connections[database]
    connection.prepare_database()
    executor = MigrationExecutor(connection)
    migrations = defaultdict(list)
    is_synchronized = True
    app_names = sorted(executor.loader.migrated_apps)
    for app_name in app_names:
        shown = set()
        for node in executor.loader.graph.leaf_nodes(app_name):
            for plan_node in executor.loader.graph.forwards_plan(node):
                if plan_node not in shown and plan_node[0] == app_name:
                    applied_migration = executor.loader.applied_migrations.get(plan_node)
                    reversible = all(
                        operation.reversible for operation in executor.loader.graph.nodes[plan_node].operations)
                    applied = applied_migration is not None
                    migrations[app_name].append({
                        'name': plan_node[1],
                        'applied': applied,
                        'reversible': reversible
                    })
                    if not applied_migration:
                        is_synchronized = False
    return is_synchronized, migrations


def unapplied_migrations(migrations):
    unapplied = []
    for app, app_migrations in migrations.items():
        for app_migration in app_migrations:
            if not app_migration['applied']:
                unapplied.append(f"{app}.{app_migration['name']}, reversible: {app_migration['reversible']}")
    return unapplied


def rollback_points(migrations):
    points = []
    for app, app_migrations in migrations.items():
        for i, app_migration in enumerate(reversed(app_migrations)):
            if app_migration['applied']:
                if i > 0:
                    points.append((app, app_migration['name']))
                break
    return points


is_synchronized, migrations = get_migration_info()
result = {
    'is_synchronized': is_synchronized,
    'migrations': migrations,
    'pending_migrations': unapplied_migrations(migrations),
    'rollback_points': rollback_points(migrations)
}
print(json.dumps(result, indent=2))
