#!/bin/sh

set -e

cd /app

python manage.py wait_for_db
python manage.py collectstatic --noinput
python manage.py crontab add
crond
python manage.py migrate
