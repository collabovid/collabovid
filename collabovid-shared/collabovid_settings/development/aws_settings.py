import os

AWS_STORAGE_BUCKET_NAME = 'collabovid'
AWS_ACCESS_KEY_ID = ''
AWS_SECRET_ACCESS_KEY = ''
AWS_S3_HOST = 'localhost'
AWS_S3_PROTOCOL = 'http'
AWS_S3_PORT = '9090'
AWS_S3_ENDPOINT_URL = f'{AWS_S3_PROTOCOL}://{AWS_S3_HOST}:{AWS_S3_PORT}'

S3_DB_EXPORT_LOCATION = 'export'

EMBEDDINGS_FILE_URL = '/static/embeddings_3d.json'
PAPER_ATLAS_IMAGES_FILE_URL = '/static/img/atlas.jpg'

AWS_SES_ACCESS_KEY_ID = os.getenv('AWS_SES_ACCESS_KEY_ID', None)
AWS_SES_SECRET_ACCESS_KEY = os.getenv('AWS_SES_SECRET_ACCESS_KEY', None)
EMAIL_BACKEND = 'django_ses.SESBackend'
AWS_SES_REGION_NAME = 'eu-central-1'
AWS_SES_REGION_ENDPOINT = 'email.eu-central-1.amazonaws.com'