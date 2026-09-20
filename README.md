# My cloud

My cloud is a webapp developed with [django framework](https://www.djangoproject.com/)
using [PostgreSQL](https://www.postgresql.org/) and running on [nginx](https://nginx.org/)
web server. My cloud allows you to handle files in a filesystem and encrypt/decrypt them using
[Shamir's Secret Sharing](https://web.mit.edu/6.857/OldStuff/Fall03/ref/Shamir-HowToShareASecret.pdf) scheme.

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

## Authentication (Google sign-in)

New users are created **only** by signing in with Google (via
[django-allauth](https://docs.allauth.org/)). Staff/superusers still log in with a
username/password through the Django admin (`/admin/`), and are created with
`./manage.py createsuperuser`. There is no local self-registration form.

To enable the "Sign in with Google" button:

1. In the [Google Cloud console](https://console.cloud.google.com/apis/credentials), create an
   **OAuth 2.0 Client ID** of type *Web application*.
2. Add the authorized redirect URI(s):
   - `http://localhost:8000/accounts/google/login/callback/` (local dev)
   - `https://<your-domain>/accounts/google/login/callback/` (production)
3. Put the credentials in your `.env`:
   ```
   GOOGLE_OAUTH_CLIENT_ID=...
   GOOGLE_OAUTH_CLIENT_SECRET=...
   ```

On the first Google sign-in the Django user is created automatically and starts with an empty,
isolated workspace (each user only sees their own folders, files and schemes). In production, also
add your domain to `ALLOWED_HOSTS`.

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

## Deploying to DigitalOcean App Platform

CI/CD is wired up in [`.github/workflows/deploy.yml`](.github/workflows/deploy.yml): on every push to
`master` it runs the test suite with a **coverage gate (`--cov-fail-under=98`)**, and only if that
passes does it build the image, push it to **DigitalOcean Container Registry (DOCR)**, and deploy to
**App Platform** (`digitalocean/app_action/deploy@v2`, by image digest). Pull requests run the tests
only.

App Platform runs a single container (no nginx — **WhiteNoise** serves static files) with an
**ephemeral disk**, so uploads/encrypted files are stored in **DigitalOcean Spaces** (set
`USE_SPACES=True`). The app talks only to Django's storage API, so locally (with `USE_SPACES` unset)
it keeps using the filesystem unchanged.

**One-time setup:**

1. **DOCR:** create a container registry. Edit the `REGISTRY` value in the workflow to
   `registry.digitalocean.com/<your-registry>`.
2. **Spaces:** create a bucket and a Spaces access key/secret.
3. **App:** edit the `<PLACEHOLDERS>` in [`.do/app.yaml`](.do/app.yaml) (bucket, region), then create
   the app once: `doctl apps create --spec .do/app.yaml`. It provisions an App Platform **dev
   database** and binds `DATABASE_URL` automatically.
4. **Secrets:** in the App Platform dashboard set the `SECRET` env vars — `SECRET_KEY`,
   `GOOGLE_OAUTH_CLIENT_ID/SECRET`, `SPACES_ACCESS_KEY/SECRET`. (CI only swaps the image, so these are
   preserved across deploys.)
5. **GitHub:** add repo secret `DIGITALOCEAN_ACCESS_TOKEN` (a DO API token).
6. **Google OAuth:** add the redirect URI `https://<app-domain>/accounts/google/login/callback/`; in
   `/admin/` set the **Site** domain; the app's domain is already wired into `ALLOWED_HOSTS` /
   `CSRF_TRUSTED_ORIGINS` via `${APP_DOMAIN}` in the spec.
7. First deploy, then create an admin with
   `doctl apps ... console` → `python manage.py createsuperuser` (or use the dashboard console).
