FROM python:3.13-slim

# Install system dependencies required by pycairo, weasyprint, and xhtml2pdf
RUN apt-get update && apt-get install -y --no-install-recommends \
    libcairo2-dev \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libgdk-pixbuf-xlib-2.0-0 \
    libffi-dev \
    shared-mime-info \
    pkg-config \
    gcc \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Run collectstatic at build time (faster startup, Railway health check won't time out)
RUN SECRET_KEY=build-only-dummy-key DJANGO_SETTINGS_MODULE=config.settings python manage.py collectstatic --noinput

CMD python manage.py migrate --noinput && python load_initial_data.py && gunicorn config.wsgi:application --bind 0.0.0.0:$PORT --timeout 120 --workers 2 --log-file -
