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
.venv/flag: pyproject.lock
	@ poetry config settings.virtualenvs.in-project true
	poetry develop
	@ touch $@

pyproject.lock: pyproject.toml
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
	poetry run pytest elections --disable-warnings
	poetry run pytest tests --disable-warnings --cov-append

.PHONY: watch
watch: install
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
data: install migrate
	poetry run python manage.py seed_data
	poetry run python manage.py crawl_mi_sos --start=1828 --limit=3 --randomize
	poetry run python manage.py fetch_mi_sos --limit=3

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
	poetry run python manage.py graph_models --all-applications --group-models --output=docs/ERD.png

###############################################################################

.PHONY: clean
clean:
	rm -rf .venv
