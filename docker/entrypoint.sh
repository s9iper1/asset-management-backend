#!/usr/bin/env bash
set -e

DB_HOST="${DB_HOST:-db}"
DB_PORT="${DB_PORT:-3306}"

echo "Waiting for MySQL at ${DB_HOST}:${DB_PORT} ..."
# requires netcat-openbsd in the image
until nc -z "${DB_HOST}" "${DB_PORT}"; do
  echo "MySQL is unavailable - sleeping"
  sleep 2
done
echo "MySQL is up!"

# Apply migrations
python manage.py migrate --noinput

# (Optional) collectstatic in non-debug
if [ "${DJANGO_DEBUG:-1}" != "1" ]; then
  python manage.py collectstatic --noinput || true
fi

# Auto-create superuser if env vars are set
if [ -n "${DJANGO_SUPERUSER_EMAIL}" ] && [ -n "${DJANGO_SUPERUSER_PASSWORD}" ] && [ -n "${DJANGO_SUPERUSER_NAME}" ]; then
  echo "Ensuring superuser ${DJANGO_SUPERUSER_EMAIL} exists..."
  python manage.py shell -c "
from django.contrib.auth import get_user_model
User = get_user_model()
email = '${DJANGO_SUPERUSER_EMAIL}'
password = '${DJANGO_SUPERUSER_PASSWORD}'
name = '${DJANGO_SUPERUSER_NAME}'
u = User.objects.filter(email=email).first()
if not u:
    print('Creating superuser', email)
    try:
        User.objects.create_superuser(email=email, password=password, name=name)
    except TypeError:
        # Fallbacks for different custom user signatures
        try:
            User.objects.create_superuser(username=email, email=email, password=password)
        except TypeError:
            User.objects.create_superuser(email=email, password=password)
else:
    print('Superuser already exists:', email)
"
fi

exec "$@"
