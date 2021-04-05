#!/bin/bash
chmod 777 -R /cache
chown -R root:root /cache
gunicorn ${PROJECT_NAME}.wsgi --user www-data --bind 0.0.0.0:8000 --workers 1 --timeout 500 & nginx -g "daemon off;"