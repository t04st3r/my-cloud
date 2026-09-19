# syntax=docker/dockerfile:1
# Self-contained image for DigitalOcean App Platform (single container, no nginx).
# Static files are served by WhiteNoise; uploaded media lives in Spaces.
FROM python:3.14-slim

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PROJECT_ENVIRONMENT=/usr/local \
    DJANGO_SETTINGS_MODULE=my_cloud.settings

# Runtime libraries: libmagic for python-magic, libpq for psycopg.
RUN apt-get update && \
    apt-get install -y --no-install-recommends libmagic1 libpq5 && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Dependencies first (better layer caching).
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

# Application code.
COPY . .

# Run as a non-root user; ensure the static output dir is writable.
RUN useradd --create-home app && mkdir -p /app/staticfiles && chown -R app /app
USER app

EXPOSE 8080

# Migrate, collect static (builds the WhiteNoise manifest), then serve.
CMD ["sh", "-c", "python manage.py migrate --noinput && python manage.py collectstatic --noinput && gunicorn my_cloud.wsgi --bind 0.0.0.0:8080 --workers 3"]
