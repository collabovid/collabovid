#!/bin/bash
python -c "import nltk; import os; nltk.download('stopwords', download_dir=os.environ['NLTK_DATA'])"
gunicorn ${PROJECT_NAME}.wsgi --user www-data --bind 0.0.0.0:8000 --workers 1  --timeout 100 & nginx -g "daemon off;"