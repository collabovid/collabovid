import os
#  This file includes the different database options dependning on a environment variable.


if int(os.getenv("USE_SQLITE_DATABASE", "0")) > 0:
    from collabovid_settings.development.sqlite_settings import *
    print("Using SQLite database")
else:
    from collabovid_settings.postgres_settings import *
    print("Using Postgres database")
