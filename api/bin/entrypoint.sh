#!/bin/bash
python manage.py migrate
gunicorn core.wsgi --bind 0.0.0.0:8000 --workers 1 --threads 1
