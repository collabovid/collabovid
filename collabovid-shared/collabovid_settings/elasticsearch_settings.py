import os
ELASTICSEARCH_DSL={
    'default': {
        'hosts': os.getenv('ELASTICSEARCH_URL', 'localhost:9200'),
        'timeout': 500
    },
}