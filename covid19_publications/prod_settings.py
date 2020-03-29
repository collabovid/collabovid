from .base_settings import *

ALLOWED_HOSTS = ['django-env.eba-3yrfmfbq.us-east-1.elasticbeanstalk.com']
SECRET_KEY = os.environ('SECRET_KEY')