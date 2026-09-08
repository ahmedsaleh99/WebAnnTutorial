# Lesson 4 — Django foundations and the first test

## Goal

Replace Lesson 3's temporary Python HTTP server with a real Django 5.2 project.
You will build one health endpoint test-first and add Python formatting, linting,
framework validation, and tests to the quality gate shared by local development
and CI.

**Branch:** `lesson/04-django-foundations`

**Prerequisite:** Lesson 3 is merged into `main`; Docker works; Python 3.12 is
available as described in [Local developer tooling](../TOOLING.md).

## What you will learn

- what Django projects and applications represent;
- how a request travels through URL configuration to a view and response;
- what settings, `manage.py`, WSGI, and application configuration do;
- how to write a failing Django test before implementing behavior;
- why configuration and secrets come from the environment;
- the difference between formatting, linting, Django system checks, and tests;
- how to run the same backend checks locally, in Docker, and in CI.

## Deliverables

- Django 5.2 LTS pinned in `backend/requirements.txt`;
- a `config` project package and `annotations` application package;
- a JSON `GET /health/` endpoint;
- a Django test proving its contract;
- environment-driven secret and debug settings;
- Ruff formatting and linting;
- backend Make targets and a shared check script;
- an updated API image and container smoke test; and
- Python dependency installation in CI.

## Part 1 — Start from the Lesson 3 checkpoint

```bash
git switch main
git pull --ff-only
make check
make container-test
git switch -c lesson/04-django-foundations
git branch --show-current
```

The final command must print `lesson/04-django-foundations`.

## Part 2 — Install Django and understand the structure

Create `backend/requirements.txt` and pin Django to the course's selected 5.2
patch release. Add the backend requirements to `requirements-dev.txt` with:

```text
-r backend/requirements.txt
```

This keeps runtime dependencies separate while installing them into the local
development environment. Also add the pinned Ruff version to the development
requirements. Re-run bootstrap whenever a requirements file changes:

```bash
make bootstrap
```

Create the initial structure:

```text
backend/
├── manage.py
├── requirements.txt
├── config/
│   ├── __init__.py
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
└── annotations/
    ├── __init__.py
    ├── apps.py
    ├── urls.py
    ├── views.py
    └── tests/
        ├── __init__.py
        └── test_health.py
```

The **project** package, `config`, owns site-wide configuration. The
**application** package, `annotations`, owns one area of domain behavior. A
project contains applications; an application should remain reusable and avoid
owning deployment-wide configuration.

Key files have distinct responsibilities:

- `manage.py` is the command-line entry point and selects the settings module.
- `settings.py` configures installed apps, middleware, database, time zone, and
  other project-wide behavior.
- project `urls.py` delegates URL prefixes to application URL configurations.
- application `urls.py` maps paths to application views.
- `views.py` turns an HTTP request into an HTTP response.
- `wsgi.py` exposes the application object to WSGI servers. Django's development
  server uses it now; a production server is introduced later.
- `apps.py` gives Django metadata for the annotations application.

## Part 3 — Write the endpoint test first (red)

Before creating the health view or URL route, write
`backend/annotations/tests/test_health.py` using Django's `TestCase` and test
client. Specify the observable contract:

1. reverse the route named `health`;
2. send `GET` to that URL;
3. assert HTTP status 200;
4. assert the exact JSON object:

```json
{"service": "api", "status": "ok"}
```

Run only the test:

```bash
DJANGO_SECRET_KEY=test-only-not-a-secret \
  .venv/bin/python backend/manage.py test annotations.tests.test_health
```

It should fail because the `health` route or view does not exist. This is the
important **red** evidence. A syntax error or missing Django installation is not
a useful red result: first fix setup problems, then capture the failure caused
by missing application behavior.

Commit the test separately if your course workflow requests visible TDD history:

```bash
git add backend/annotations/tests/test_health.py
git commit -m "test: define the API health contract"
```

## Part 4 — Implement the smallest passing endpoint (green)

Create a `health` view returning Django's `JsonResponse`. Map it to `health/` in
the application URL configuration and give the route the name `health`. Include
the application's URL configuration from the project URL configuration.

The request path is:

```text
GET /health/
  → config.urls
  → annotations.urls
  → annotations.views.health
  → JsonResponse
  → HTTP 200 JSON
```

Run the test again. It must pass. Then run Django's built-in configuration
validation:

```bash
DJANGO_SECRET_KEY=test-only-not-a-secret \
  .venv/bin/python backend/manage.py check
```

`check` detects framework configuration problems. It does not replace tests:
the system can be validly configured while returning the wrong JSON.

## Part 5 — Make configuration explicit

In `config/settings.py`, read `DJANGO_SECRET_KEY` from `os.environ` with no
committed production default. Read `DJANGO_DEBUG` as an explicit boolean and
read allowed hosts from a comma-separated `DJANGO_ALLOWED_HOSTS` value.
Read the SQLite path from `DJANGO_DATABASE_PATH`, with `backend/db.sqlite3` as
the local default. Compose sets it to `/tmp/db.sqlite3`, a location writable by
the non-root container user.

For this lesson, use SQLite at `backend/db.sqlite3`. It requires no extra
service and lets the lesson focus on Django's request lifecycle. The file is
ignored and disposable. Lesson 5 replaces it with PostgreSQL and teaches
relational persistence.

The Compose file may contain an obvious value such as
`insecure-compose-development-key`; its name and value must make clear that it
is only local development configuration. Production secrets belong in a
deployment environment, never Git.

Compose must also include `api` in `DJANGO_ALLOWED_HOSTS`. The frontend contacts
the backend by that service name, and Django rejects unapproved HTTP host names.

Try the failure deliberately:

```bash
env -u DJANGO_SECRET_KEY .venv/bin/python backend/manage.py check
```

Django should stop because required configuration is missing. This is safer
than silently running production with a secret committed in source code.

## Part 6 — Add formatting and linting

Create `pyproject.toml` and configure Ruff for Python 3.12. Enable a small,
explainable rule set:

- `E`: style errors;
- `F`: likely Python mistakes, such as unused imports;
- `I`: import ordering;
- `UP`: modern Python syntax.

Run the two separate operations:

```bash
.venv/bin/ruff format --check backend
.venv/bin/ruff check backend
```

Formatting answers “is code laid out consistently?” Linting answers “does code
match selected correctness and maintainability rules?” Neither proves behavior,
which is why the Django test remains necessary.

To experience another red-green cycle, add an unused import and run Ruff. Watch
linting fail, remove it, and run the command again. `ruff format backend` may be
used to apply formatting; `ruff check --fix backend` should be used only after
reading the proposed changes.

Ruff is introduced in this lesson—not Lesson 2—because the repository now has
real Python code against which students can observe and understand its rules.

## Part 7 — Extend the shared quality gate

Create executable `scripts/check-backend.sh`. It should:

1. move to the repository root;
2. explain that `make bootstrap` is required if `.venv` tools are absent;
3. provide a test-only secret through the environment;
4. run Ruff's format check;
5. run Ruff linting;
6. run `manage.py check`;
7. run the complete Django test suite.

Add it to `scripts/check` and to the executable-file validation loop. Add these
Make targets:

```text
make backend-check
make backend-test
make backend-run
```

`backend-run` starts the development server with explicitly local settings. It
is for development only, not production serving. Run:

```bash
make backend-check
make check
```

The order intentionally puts fast formatting and lint checks before framework
startup and tests.

## Part 8 — Replace the placeholder API container

Delete `backend/server.py`. Update `backend/Dockerfile` to:

1. copy `requirements.txt` first;
2. install it without a pip download cache;
3. copy the Django source;
4. retain the non-root application user;
5. run `python manage.py runserver 0.0.0.0:8000`.

Copying requirements before source allows Docker to reuse the dependency layer
when only application code changes. Extend `.dockerignore` for `.env`, Ruff
caches, and SQLite data.

Update Compose to supply the development Django settings. Remove the Lesson 3
visit volume: its teaching purpose is complete, and PostgreSQL will introduce
real persistence in Lesson 5. Update the smoke test to retain these relevant
contracts:

- Django API health;
- frontend health;
- frontend-to-Django communication using Compose DNS.

Run:

```bash
make container-test
```

## Part 9 — Teach CI how to install Python dependencies

The repository validation job now runs Python checks, so insert these steps
before `make check`:

1. `actions/setup-python` using `.python-version`;
2. pip caching keyed by both requirements files;
3. `make bootstrap`.

Keep `make check` as the CI entry point. YAML should orchestrate the environment,
not duplicate local quality commands. The container-smoke job remains separate
because it builds and tests the full stack.

## Part 10 — Verify and open the pull request

Run:

```bash
make check
make container-test
git diff --check
git status --short
```

Start the backend manually and visit <http://127.0.0.1:8000/health/>:

```bash
make backend-run
```

Open a pull request titled `Lesson 4: add Django foundations`. Include:

- the meaningful failing test output from Part 3;
- the passing backend and container results;
- an explanation of project versus application;
- an explanation of formatting versus linting versus testing;
- the manual endpoint result;
- confirmation that no secret or SQLite database is tracked.

## Acceptance criteria

- `GET /health/` returns HTTP 200 and the exact documented JSON.
- The endpoint has a focused Django test that was observed failing first.
- `DJANGO_SECRET_KEY` is required from the environment.
- Debug behavior is controlled by the environment.
- Ruff formatting and linting pass.
- `manage.py check` and all Django tests pass.
- `make check` runs all repository, shell, Compose, and backend checks.
- The Docker stack becomes healthy and the frontend reaches Django.
- CI installs pinned dependencies and invokes the same local check target.
- `.env`, `db.sqlite3`, caches, and virtual environments remain untracked.

## Gold-standard implementation

Read this only after implementing the lesson and opening your pull request. The
instructor publishes the completed checkpoint as tag `lesson-04`.

```bash
git fetch --tags
git diff lesson-04 -- . ':!docs/lessons/04-DJANGO-FOUNDATIONS.md'
```

The reference implementation uses Django 5.2 LTS, a small `config` project, an
`annotations` application, environment-driven settings, a test-first JSON
health endpoint, Ruff, one backend quality script, and the same check entry point
locally and in CI. Its Docker image installs requirements in a cache-friendly
layer and continues running as a non-root user.

Your implementation does not need identical formatting or helper names. It
should expose the same contract, enforce the same safety properties, give useful
failure messages, and meet every acceptance criterion. Explain intentional
differences during self-review.

## What you should now be able to explain

- Django project versus Django application;
- settings, URL configuration, view, request, and response;
- `manage.py check` versus a behavioral test;
- why a test must fail for the expected reason during TDD;
- why secrets come from the environment;
- formatter versus linter;
- dependency-layer ordering in a Dockerfile; and
- why local commands and CI commands should share one entry point.
