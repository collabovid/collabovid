#!/bin/bash
chmod 777 -R /models
chown -R root:root /models
echo "Changed permissions for /models"
gunicorn ${PROJECT_NAME}.wsgi --user www-data --bind 0.0.0.0:80 --workers 1  --timeout 500