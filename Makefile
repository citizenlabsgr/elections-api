.PHONY: all
all: install

.PHONY: install
install: .venv/flag
.venv/flag: pyproject.lock requirements.txt
	@ poetry config settings.virtualenvs.in-project true
	poetry develop
	@ touch $@

pyproject.lock: pyproject.toml
	poetry lock

requirements.txt: pyproject.lock
	@ rm -f $@
	@ echo "# Generated file for Heroku deployment" >> $@
	poetry run pip freeze | grep -vwE "(pync|MacFSEvents)" >> $@

###############################################################################

.PHONY: run
run: install
	poetry run python elections/app.py

###############################################################################

PACKAGES := elections tests

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

.PHONY: clean
clean:
	rm -rf .venv
