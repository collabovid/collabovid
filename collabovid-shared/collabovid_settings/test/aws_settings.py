import os

AWS_S3_OBJECT_PARAMETERS = {
    'Expires': 'Thu, 31 Dec 2099 20:00:00 GMT',
    'CacheControl': 'max-age=94608000',
}

AWS_STORAGE_BUCKET_NAME = 'test'
AWS_S3_REGION_NAME = 'us-east-1'  # e.g. us-east-2
AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID', '')
AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY', None)

AWS_S3_ENDPOINT_URL = 'http://s3.default.svc.cluster.local'
AWS_S3_CUSTOM_DOMAIN = '%s.s3.default.svc.cluster.local' % AWS_STORAGE_BUCKET_NAME

MEDIAFILES_LOCATION = 'media'
DEFAULT_FILE_STORAGE = 'storage.custom_storage.MediaStorage'