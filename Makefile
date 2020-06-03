.PHONY: all
all: install

# SYSTEM DEPENENDENCIES #######################################################

.PHONY: doctor
doctor: ## System | Check for the required system dependencies
	bin/verchew --exit-code

.PHONY: .envrc
.envrc:
	echo "export PYTHONBREAKPOINT=ipdb.set_trace" >> $@
	echo >> $@
	echo "export REDIS_URL=redis://localhost:6379" >> $@

# PROJECT DEPENDENCIES ########################################################

.PHONY: install
install: .venv/flag ## Project | Install project dependencies
.venv/flag: poetry.lock runtime.txt requirements.txt
	@ poetry config virtualenvs.in-project true
	poetry install
	@ mkdir -p staticfiles
	@ touch $@

ifndef CI

poetry.lock: pyproject.toml
	poetry lock
	@ touch $@

runtime.txt: .python-version
	echo "python-$(shell cat $<)" > $@

requirements.txt: poetry.lock
	poetry export --format requirements.txt --output $@ --without-hashes

endif

.PHONY: clean
clean:
	rm -rf .venv

# LOCAL COMMANDS ##############################################################

.PHONY: run
run: install migrate ## Project | Run the development server
	@ echo
	poetry run python manage.py runserver

.PHONY: shell
shell: install migrate  ## Project | Open the Django shell
	@ echo
	poetry run python manage.py shell_plus

# VALIDATION COMMANDS #########################################################

PACKAGES := config elections tests

.PHONY: ci
ci: check test ## CI | Run all validation targets

.PHONY: format
format: install ## CI | Format the code
	poetry run isort $(PACKAGES) --recursive --apply
	poetry run black $(PACKAGES)

.PHONY: check
check: format ## CI | Run static analysis
	@ echo
ifdef CI
	git diff --exit-code
endif
	poetry run mypy $(PACKAGES) --config-file=.mypy.ini
	poetry run pylint $(PACKAGES) --rcfile=.pylint.ini

.PHONY: test
test: install ## CI | Run all tests
	poetry run pytest elections tests
	poetry run coveragespace citizenlabsgr/elections-api overall --exit-code

.PHONY: watch
watch: install
	@ rm -f .cache/v/cache/lastfailed
	poetry run ptw

.PHONY: notebook
notebook: install
	poetry run jupyter notebook --notebook-dir=notebooks --browser=safari

# DATA COMMANDS ###############################################################

.PHONY: migrations
migrations: install  ## Data | Generate database migrations
	poetry run python manage.py makemigrations

.PHONY: migrate
migrate: install ## Data | Run database migrations
	poetry run python manage.py migrate
	@ echo
	poetry run python manage.py migrate_data

.PHONY: data
data: migrate ## Data | Seed data for manual testing
	@ echo
	poetry run python manage.py seed_data
	@ echo
	poetry run python manage.py scrape_data --start-precinct=1828 --ballot-limit=5
	@ echo
	poetry run python manage.py parse_data

.PHONY: data/reset
data/reset: install ## Data | Create a new database, migrate, and seed it
	- dropdb elections_dev
	createdb elections_dev
	@ echo
	@ make data

.PHONY: data/production
data/production: install ## Data | Pull data as it exists on production
	- dropdb elections_dev
	heroku pg:pull DATABASE_URL elections_dev

.PHONY: uml
uml: install
	poetry run pyreverse elections -p elections -a 1 -f ALL -o png --ignore admin.py,migrations,management,tests
	mv -f classes_elections.png docs/classes.png
	mv -f packages_elections.png docs/packages.png
	poetry run python manage.py graph_models elections --group-models --output=docs/tables.png --exclude-models=TimeStampedModel

# HELP ########################################################################

.PHONY: help
help: all
	@ grep -E '^[a-zA-Z/_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'

.DEFAULT_GOAL := help
