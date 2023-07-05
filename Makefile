migrate:
	python manage.py migrate --noinput

lint:
	ruff check .

test:
	pytest

ci: migrate lint test

dump-requirements:
	jq -r '.default | to_entries[] | .key + .value.version' Pipfile.lock > requirements.txt
	jq -r '.develop | to_entries[] | .key + .value.version' Pipfile.lock > requirements-dev.txt	

install:
	pip install -r requirements.txt

install-dev:
	pip install -r requirements-dev.txt --pre

install-ci: dump-requirements install install-dev

collectstatic:
	python manage.py collectstatic --noinput

run-dev:
	python manage.py runserver	