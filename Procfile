web: python manage.py migrate --noinput && python load_initial_data.py && python manage.py collectstatic --noinput && gunicorn config.wsgi:application --bind 0.0.0.0:$PORT --log-file -
