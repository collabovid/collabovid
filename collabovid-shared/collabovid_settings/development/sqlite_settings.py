import os

DEV_DATABASE_LOCATION = os.getenv('DEV_DATABASE_LOCATION',
                                  os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                                               '../../db.sqlite3'))

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': DEV_DATABASE_LOCATION,
    }
}
