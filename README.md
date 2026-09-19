# My cloud

My cloud is a webapp developed with [django framework](https://www.djangoproject.com/)
using [PostgreSQL](https://www.postgresql.org/) and running on [nginx](https://nginx.org/)
web server. My cloud allows you to handle files in a filesystem and encrypt/decrypt them using
[Shamir's Secret Sharing](https://web.mit.edu/6.857/OldStuff/Fall03/ref/Shamir-HowToShareASecret.pdf) scheme.

**Warning**

This app has been developed for demonstration purposes, is not meant to be used in production.

## Tech stack

- Python 3.14 (managed with [uv](https://docs.astral.sh/uv/))
- Django 5.2 (LTS) + Django REST Framework
- PostgreSQL 17 (via [psycopg 3](https://www.psycopg.org/psycopg3/))
- Configuration via environment variables ([django-environ](https://django-environ.readthedocs.io/))

## Local development

Run Postgres in a container and the Django app directly on your machine.

### Prerequisites

1. [uv](https://docs.astral.sh/uv/getting-started/installation/)
2. Docker with the Compose plugin (`docker compose`)
3. The `libmagic` system library (used by `python-magic`) — e.g. on Debian/Ubuntu:
   `sudo apt install libmagic1`
4. Optional: [direnv](https://direnv.net) to auto-activate the virtualenv (see below)

### Steps

Clone the repository and enter it:

```
$ git clone https://github.com/t04st3r/my-cloud.git
$ cd my-cloud
```

Install dependencies (uv creates a `.venv` and installs Python 3.14 automatically):

```
$ uv sync
```

Start the PostgreSQL container:

```
$ docker compose -f docker-compose-dev.yaml up -d
```

Apply migrations, create a superuser and run the development server:

```
$ uv run ./manage.py migrate
$ uv run ./manage.py createsuperuser
$ uv run ./manage.py runserver
```

The app is now available at `http://localhost:8000`.

Configuration has sensible local defaults, so no `.env` file is required. To
override any setting, copy `.env.example` to `.env` and edit it.

### Tests

The suite uses **pytest** (`pytest-django`, `pytest-xdist`, `pytest-cov`) with
**factory_boy** factories. Tests run against a temporary, per-test `MEDIA_ROOT`, so
they never touch the real `media/` folder and are fully idempotent. A running
Postgres container (the dev compose above) is required — pytest creates and drops a
`test_postgres` database.

```
$ uv run pytest            # parallel (xdist) + coverage report
$ uv run pytest -n0        # serial, clearest output for debugging
```

A coverage summary is printed to the terminal and an HTML report is written to
`htmlcov/index.html`.

Stop the database container when you are done:

```
$ docker compose -f docker-compose-dev.yaml down
```

### Auto-activating the virtualenv with direnv (optional)

The repository ships an `.envrc` so that [direnv](https://direnv.net) keeps the
uv environment in sync and activates it whenever you `cd` into the project (and
deactivates it when you leave). With direnv installed and hooked into your shell,
trust the file once:

```
$ direnv allow
```

From then on the `.venv` is on your `PATH` inside the project, so you can drop the
`uv run` prefix:

```
$ ./manage.py migrate
$ ./manage.py runserver
$ ./manage.py test
```

(The `uv run` form still works everywhere — in CI, or if you don't use direnv.)

## Production-like stack (nginx + gunicorn + postgres)

The `docker/` folder contains a full stack served by nginx in front of gunicorn.

```
$ cd docker
$ docker compose build
$ docker compose up -d
```

Test the webapp is up and running by connecting on `http://localhost:8000`
with your favorite browser.

Create a superuser:

```
$ docker exec -it django01 python manage.py createsuperuser
```

Set `SECRET_KEY`, `POSTGRES_PASSWORD` and `ALLOWED_HOSTS` in the environment (or
a `.env` file next to `docker/docker-compose.yml`) before exposing it anywhere.

You are good to go now!
