.PHONY: all
all: install

###############################################################################

.PHONY: doctor
doctor:
	bin/verchew --exit-code

.PHONY: .envrc
.envrc:
	echo "export REDIS_URL=redis://localhost:6379" >> $@

###############################################################################

.PHONY: install
install: .venv/flag
.venv/flag: poetry.lock
	@ poetry config settings.virtualenvs.in-project true
	poetry install
	@ touch $@

poetry.lock: pyproject.toml
	poetry lock
	@ touch $@

###############################################################################

.PHONY: run
run: install migrate
	poetry run python manage.py runserver

###############################################################################

PACKAGES := config elections scripts tests

.PHONY: ci
ci: check test

.PHONY: format
format: install
	poetry run isort $(PACKAGES) --recursive --apply
	poetry run black $(PACKAGES) --line-length=79 --py36 --skip-string-normalization

.PHONY: check
check: install
	poetry run pylint $(PACKAGES) --rcfile=.pylint.ini
	poetry run mypy $(PACKAGES) --config-file=.mypy.ini

.PHONY: test
test: install
	@ rm -f .cache/coverage*
	poetry run pytest elections
	poetry run pytest tests --cov-append --maxfail=1 --failed-first

.PHONY: watch
watch: install
	rm -f cache.sqlite
	poetry run ptw

###############################################################################

.PHONY: migrations
migrations: install
	poetry run python manage.py makemigrations

.PHONY: migrate
migrate: install
	poetry run python manage.py migrate
	poetry run python manage.py migrate_data

.PHONY: data
data: migrate
	poetry run python manage.py seed_data
	poetry run python manage.py scrape_data --start=1828 --limit=5
	poetry run python manage.py clean_data
	poetry run python manage.py scrape_data --start=1828 --limit=5

.PHONY: scrape
scrape: data
	poetry run python manage.py scrape_data

.PHONY: reset
reset: install
	dropdb elections_dev; createdb elections_dev
	make data

.PHONY: readme
readme: install elections/templates/index.html
elections/templates/index.html: README.md scripts/render_readme.py
	poetry run readme $< $@

.PHONY: uml
uml: install
	poetry run python manage.py graph_models elections --group-models --output=docs/ERD.png --exclude-models=TimeStampedModel

###############################################################################

.PHONY: clean
clean:
	rm -rf .venv
