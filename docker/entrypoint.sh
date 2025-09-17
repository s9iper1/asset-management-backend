#!/usr/bin/env bash
set -e

DB_HOST="${DB_HOST:-db}"
DB_PORT="${DB_PORT:-3306}"

echo "Waiting for MySQL at $DB_HOST:$DB_PORT ..."
until mysqladmin ping -h"$DB_HOST" -P"$DB_PORT" --silent; do
  sleep 2
  echo "MySQL is unavailable - sleeping"
done
echo "MySQL is up!"

# Apply migrations
python manage.py migrate --noinput

# Auto-create superuser if env vars are set
if [ -n "$DJANGO_SUPERUSER_EMAIL" ] && [ -n "$DJANGO_SUPERUSER_PASSWORD" ] && [ -n "$DJANGO_SUPERUSER_NAME" ]; then
python <<'PYCODE'
import os
from django.contrib.auth import get_user_model
User = get_user_model()
email = os.environ["DJANGO_SUPERUSER_EMAIL"]
password = os.environ["DJANGO_SUPERUSER_PASSWORD"]
name = os.environ["DJANGO_SUPERUSER_NAME"]
if not User.objects.filter(email=email).exists():
    print(f"Creating superuser {email}")
    User.objects.create_superuser(email=email, password=password, name=name)
else:
    print("Superuser already exists")
PYCODE
fi

exec "$@"
