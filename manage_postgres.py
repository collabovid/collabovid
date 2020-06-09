import os
import subprocess
import sys
from datetime import datetime

dump_dir = "resources/postgres_backup"
db_name = "collabovid"

commands = ("dump", "clear", "load", "reset", "deletedumps")


def stderr(msg):
    sys.stderr.write(msg)
    sys.stderr.flush()


def dump():
    now = datetime.strftime(datetime.now(), "%Y-%m-%d-%H%M")
    sql_file = f"dbdump_{now}.sql"
    path = f"{dump_dir}/{sql_file}"

    os.makedirs(dump_dir, exist_ok=True)

    with open(path, "w") as out_file:
        res = subprocess.run(["pg_dump", db_name], stdout=out_file)

    if res.returncode != 0:
        stderr("Failed to create db dump")
        exit(1)


def get_dumpfiles():
    if not os.path.exists(dump_dir):
        print(f"No such directory: {dump_dir}")
        exit(0)

    dump_files = sorted(os.listdir(dump_dir), reverse=True)

    if len(dump_files) == 0:
        print("No dumps available")
        exit(0)

    return dump_files


def print_dumpfiles(dumpfiles):
    for i, filename in enumerate(dumpfiles):
        print("{:2d}. {}".format(i, filename))


def load():
    dumpfiles = get_dumpfiles()

    print_dumpfiles(dumpfiles)

    idx = -1
    while idx not in range(len(dumpfiles)):
        try:
            idx = int(input(f"Specify dump (0 - {len(dumpfiles) - 1}): "))
        except ValueError:
            continue

    path = f"{dump_dir}/{dumpfiles[idx]}"
    with open(path, "r") as in_file:
        res = subprocess.run(["psql", db_name], stdin=in_file)

    if res.returncode != 0:
        stderr("Failed to load db dump")
        exit(1)


def clear():
    res = subprocess.run(["dropdb", db_name])
    if res.returncode != 0:
        stderr(f"Failed to drop database {db_name}")
        exit(1)

    res = subprocess.run(["createdb", db_name])
    if res.returncode != 0:
        stderr(f"Failed to create database {db_name}")
        exit(1)


def deletedumps():
    dumpfiles = get_dumpfiles()

    print_dumpfiles(dumpfiles)
    print(" A. All")
    print(" B. All except latest")

    idx = -1
    while idx not in ("A", "B") and idx not in range(len(dumpfiles)):
        idx = input(f"Specify dump (0 - {len(dumpfiles) - 1}, A, B): ")
        if idx not in ("A", "B"):
            try:
                idx = int(idx)
            except ValueError:
                pass

    if idx == "A":
        for filename in dumpfiles:
            os.remove(f"{dump_dir}/{filename}")
    if idx == "B":
        for filename in dumpfiles[1:]:
            os.remove(f"{dump_dir}/{filename}")
    else:
        os.remove(f"{dump_dir}/{dumpfiles[idx]}")


command = sys.argv[1] if len(sys.argv) > 1 else None
while command not in commands:
    command = input(f"Specify command ({'/'.join(commands)}): ")

if command == "dump":
    dump()
elif command == "clear":
    clear()
elif command == "load":
    load()
elif command == "reset":
    clear()
    load()
elif command == "deletedumps":
    deletedumps()