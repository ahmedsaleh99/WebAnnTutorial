.PHONY: help bootstrap hooks check validate shell-check verify-python

PYTHON ?= python3
VENV := .venv
PRE_COMMIT := $(VENV)/bin/pre-commit

help:
	@echo "Available targets:"
	@echo "  bootstrap   Create the tooling environment and install dependencies"
	@echo "  hooks       Install the Git pre-commit hook"
	@echo "  check       Run every quality check available in this lesson"
	@echo "  validate    Validate repository policy"
	@echo "  shell-check Check shell scripts for syntax errors"

bootstrap: $(PRE_COMMIT)

verify-python:
	@./scripts/check-python-runtime.sh "$(PYTHON)"

$(PRE_COMMIT): requirements-dev.txt | verify-python
	$(PYTHON) -m venv $(VENV)
	$(VENV)/bin/python -m pip install --upgrade pip
	$(VENV)/bin/python -m pip install --requirement requirements-dev.txt

hooks: bootstrap
	$(PRE_COMMIT) install

check:
	./scripts/check

validate:
	./scripts/validate-repository.sh

shell-check:
	./scripts/check-shell.sh
