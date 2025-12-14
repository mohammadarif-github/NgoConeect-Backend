#!/usr/bin/env bash
# build.sh - Render build script

set -o errexit

# Install dependencies
pip install -r requirements.txt

# Go to Django project directory
cd ngoconnect

# Collect static files
python manage.py collectstatic --noinput

# Run migrations
python manage.py migrate