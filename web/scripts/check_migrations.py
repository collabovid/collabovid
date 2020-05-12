import django
django.setup()

from django.db.migrations.executor import MigrationExecutor
from django.db import connections, DEFAULT_DB_ALIAS
from io import StringIO
from django.core.management import call_command
import json


def is_database_synchronized(database):
    connection = connections[database]
    connection.prepare_database()
    executor = MigrationExecutor(connection)
    targets = executor.loader.graph.leaf_nodes()
    return not executor.migration_plan(targets)


def get_pending_migrations():
    result = []
    out = StringIO()
    call_command('showmigrations', format="plan", stdout=out)
    out.seek(0)
    for line in out.readlines():
        status, name = line.rsplit(' ', 1)
        status = status.strip() == '[X]'
        if not status:
            result.append(name.strip())
    return result


result = {
    'is_synchronized': is_database_synchronized(DEFAULT_DB_ALIAS),
    'pending_migrations': get_pending_migrations()
}

print(json.dumps(result))
