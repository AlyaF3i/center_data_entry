#!/bin/sh
set -e

# Only do this on the very first start of the container
if [ ! -f /app/.initialized ]; then
  echo "=> Running migrations…"
  python manage.py migrate --noinput

  echo "=> Importing excel/data.xlsx as 'ACTIVE PED'…"
  python manage.py import_sheet "excel/data.xlsx" "ACTIVE PED"

  # create the marker so we don't run again
  touch /app/.initialized
fi

echo "=> Launching Gunicorn…"
exec gunicorn employee_site.wsgi:application \
     --workers 3 \
     --bind 0.0.0.0:8000
