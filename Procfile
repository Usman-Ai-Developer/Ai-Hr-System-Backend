web: python manage.py migrate --noinput && python manage.py collectstatic --noinput && gunicorn ai_hr_system.wsgi:application --bind 0.0.0.0:$PORT --workers 2 --timeout 120
worker: celery -A ai_hr_system worker --loglevel=info --concurrency=2
