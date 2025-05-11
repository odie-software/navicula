#!/bin/bash
python manage.py migrate
gunicorn config.wsgi --bind 0.0.0.0:8000 --workers 4 --threads 4
