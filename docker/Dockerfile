# syntax=docker/dockerfile:1
FROM python:3.14-slim

# uv: fast, reproducible dependency management from pyproject.toml + uv.lock
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PROJECT_ENVIRONMENT=/usr/local

# Runtime libraries: libmagic for python-magic, libpq for psycopg.
RUN apt-get update && \
    apt-get install -y --no-install-recommends libmagic1 libpq5 && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /src

# Install dependencies first (better layer caching). The build context is the
# repository root (see docker-compose.yml), so pyproject.toml and uv.lock are
# at the context root.
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

# Application code is mounted as a volume by docker-compose.yml.
