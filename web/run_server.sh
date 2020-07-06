#!/bin/bash
gunicorn ${PROJECT_NAME}.wsgi --user www-data --bind 0.0.0.0:8000 --workers 1 --timeout 500 & nginx -g "daemon off;"