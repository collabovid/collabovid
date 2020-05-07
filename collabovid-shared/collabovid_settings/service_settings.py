import os

SEARCH_SERVICE_HOST = os.getenv('WEB_SERVICE_HOST', 'web.default.svc.cluster.local')
WEB_SERVICE_HOST = os.getenv('SEARCH_SERVICE_HOST', 'search.default.svc.cluster.local')

WEB_SERVICE_URL = "http://" + WEB_SERVICE_HOST + ":80"
SEARCH_SERVICE_URL = "http://"+SEARCH_SERVICE_HOST+":80"
