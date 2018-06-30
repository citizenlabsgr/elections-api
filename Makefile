.PHONY: all
all: install

###############################################################################

.PHONY: doctor
doctor:
	@ pip install --user verchew && verchew --exit

###############################################################################

.PHONY: install
install: .venv/flag
.venv/flag: pyproject.lock
	@ poetry config settings.virtualenvs.in-project true
	poetry develop
	@ touch $@

pyproject.lock: pyproject.toml
	poetry lock

###############################################################################

.PHONY: run
run: install
	poetry run python manage.py runserver

###############################################################################

PACKAGES := config elections tests

.PHONY: ci
ci: check test

.PHONY: format
format: install
	poetry run isort $(PACKAGES) --recursive --apply
	poetry run black $(PACKAGES) --line-length=79 --py36

.PHONY: check
check: install
	poetry run isort $(PACKAGES) --recursive --check-only --diff
	poetry run pylint $(PACKAGES) --rcfile=.pylint.ini
	poetry run mypy $(PACKAGES) --config-file=.mypy.ini

.PHONY: test
test: install
	poetry run pytest

.PHONY: watch
watch: install
	poetry run rerun "make test format check" -i .coverage -i htmlcov

###############################################################################

.PHONY: migrations
migrations: install
	poetry run python manage.py makemigrations

.PHONY: data
data: install
	poetry run python manage.py migrate
	poetry run python manage.py gendata

.PHONY: reset
reset: install
	dropdb elections_dev; createdb elections_dev
	make data

###############################################################################

.PHONY: clean
clean:
	rm -rf .venv
