================
Collabovid-Shared
================

Collabovid-Shared contains web-based Django apps that
contain models and classes that need to be shared
between all Collabovid services.

Quick start
-----------

1. Add "data" and "tasks to your INSTALLED_APPS setting like this::

    INSTALLED_APPS = [
        ...
        'tasks',
        'data',
    ]
2. Run ``python manage.py migrate`` to create the data and tasks models.