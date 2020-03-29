from .base_settings import *

ALLOWED_HOSTS = ['ec2-34-207-115-70.compute-1.amazonaws.com']
SECRET_KEY = os.environ['SECRET_KEY']