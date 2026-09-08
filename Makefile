.PHONY: backend-check backend-run backend-test bootstrap check container-check container-test hooks shell-check validate verify-python

PYTHON ?= python3
VENV := .venv
PRE_COMMIT := $(VENV)/bin/pre-commit

help:
	@echo "Available targets:"
	@echo "  bootstrap   Create the tooling environment and install dependencies"
	@echo "  hooks       Install the Git pre-commit hook"
	@echo "  check       Run every quality check available in this lesson"
	@echo "  backend-check Format, lint, validate, and test the Django backend"
	@echo "  backend-test  Run the Django test suite"
	@echo "  backend-run   Start Django's local development server"
	@echo "  container-check Validate the Docker Compose configuration"
	@echo "  container-test  Build and smoke-test the container stack"
	@echo "  validate    Validate repository policy"
	@echo "  shell-check Check shell scripts for syntax errors"

bootstrap: $(PRE_COMMIT)

verify-python:
	@./scripts/check-python-runtime.sh "$(PYTHON)"

$(PRE_COMMIT): requirements-dev.txt backend/requirements.txt | verify-python
	$(PYTHON) -m venv $(VENV)
	$(VENV)/bin/python -m pip install --upgrade pip
	$(VENV)/bin/python -m pip install --requirement requirements-dev.txt

hooks: bootstrap
	$(PRE_COMMIT) install

check:
	./scripts/check

backend-check:
	./scripts/check-backend.sh

backend-test: bootstrap
	DJANGO_SECRET_KEY=test-only-not-a-production-secret $(VENV)/bin/python backend/manage.py test annotations

backend-run: bootstrap
	DJANGO_SECRET_KEY=insecure-local-development-key DJANGO_DEBUG=true $(VENV)/bin/python backend/manage.py runserver

container-check:
	./scripts/check-compose.sh

container-test:
	./scripts/test-containers.sh

validate:
	./scripts/validate-repository.sh

shell-check:
	./scripts/check-shell.sh
