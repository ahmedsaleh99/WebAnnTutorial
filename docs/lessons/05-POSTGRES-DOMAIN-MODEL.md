# Lesson 5 — PostgreSQL, models, and migrations

## Goal

Replace disposable container SQLite with PostgreSQL and model the first WebAnn
domain: reusable project templates, projects, annotation dimensions and labels,
and subjects. Define invariants as failing tests before implementing models and
database constraints.

**Branch:** `lesson/05-postgres-domain-model`

**Prerequisite:** Lesson 4 is merged and tagged; `make check` and
`make container-test` pass.

## Deliverables

- PostgreSQL and a persistent volume in Compose;
- Psycopg, Django's PostgreSQL driver;
- five related Django models with UUID identifiers;
- database uniqueness, check, cascade, and protect behavior;
- reusable test builders and model tests;
- a generated and reviewed initial migration;
- automatic container migration and migration-drift checking;
- PostgreSQL-backed CI tests; and
- a documented entity-relationship model.

## Part 1 — Create the lesson branch

```bash
git switch main
git pull --ff-only
make check
make container-test
git switch -c lesson/05-postgres-domain-model
```

## Part 2 — Design relationships before tables

Create `docs/DATA_MODEL.md`. Draw and explain these relationships:

```text
ProjectTemplate 1 ── many Project
Project         1 ── many AnnotationDimension
Dimension       1 ── many AnnotationLabel
Project         1 ── many Subject
```

Decide the invariants before writing fields:

- template key and version are unique together;
- project key is globally unique;
- dimension key is unique inside its project;
- label name is unique inside its dimension;
- subject ID is unique inside its project;
- template deletion is protected while projects use it;
- project deletion removes its owned dimensions, labels, and subjects.

A foreign key stores identity and lets PostgreSQL preserve referential
integrity. `PROTECT` represents a referenced definition that must survive;
`CASCADE` represents a child owned by its parent.

## Part 3 — Write model tests first (red)

Create `backend/annotations/tests/builders.py` with small functions such as
`create_template`, `create_project`, and `create_dimension`. Builders provide
valid defaults and accept overrides. They keep each test focused on the one fact
it changes; unlike fixtures, the setup remains visible Python.

Create `test_models.py` and specify:

1. duplicate template key/version raises `IntegrityError`;
2. an in-use template raises `ProtectedError` on deletion;
3. an unknown project status fails `full_clean()`;
4. duplicate dimension keys fail within one project but work across projects;
5. duplicate label names fail within one dimension;
6. malformed label colors fail `full_clean()`;
7. duplicate subject IDs fail within one project;
8. deleting a project cascades to owned records.

Use `transaction.atomic()` around an expected `IntegrityError`. PostgreSQL marks
the current transaction broken after a constraint error; the inner atomic block
provides a savepoint Django can roll back before the test continues.

Run:

```bash
make backend-test
```

The test should fail because the models do not exist. That is the useful red
result. Record it in the PR.

## Part 4 — Implement the smallest relational model (green)

Create `annotations/models.py` with `ProjectTemplate`, `Project`,
`AnnotationDimension`, `AnnotationLabel`, and `Subject`.

Use:

- `UUIDField` primary keys so identity is not tied to one database sequence;
- `ForeignKey` plus meaningful `related_name` values for reverse traversal;
- `TextChoices` for project status;
- `JSONField(default=dict)` only for flexible configuration/attributes;
- `UniqueConstraint` for scoped compound uniqueness;
- `CheckConstraint` for database-valid template versions and statuses;
- `RegexValidator` for the user-facing label-color rule;
- deterministic `Meta.ordering`; and
- useful `__str__` methods.

Do not put dimensions, labels, or subjects into JSON. They have identity,
relationships, ordering, and uniqueness rules, so relational tables are the
correct representation.

## Part 5 — Generate and inspect the migration

Generate the schema transition from the model state:

```bash
DJANGO_SECRET_KEY=test-only-not-a-secret \
  .venv/bin/python backend/manage.py makemigrations annotations
```

Open `backend/annotations/migrations/0001_initial.py`. Confirm every table,
foreign key, deletion policy, and named constraint matches the design. A
migration is version-controlled schema history, not generated clutter.

Run the tests again, then ensure models and migrations agree:

```bash
DJANGO_SECRET_KEY=test-only-not-a-secret \
  .venv/bin/python backend/manage.py makemigrations --check --dry-run
```

Add that drift check to `scripts/check-backend.sh`. CI must fail if someone
changes a model without committing its migration.

## Part 6 — Add PostgreSQL to Compose

Add `psycopg[binary]` to `backend/requirements.txt`. In settings, select the
PostgreSQL backend when `POSTGRES_DB` is present and read database name, user,
password, host, and port from environment variables. Retain SQLite as the
zero-service local fallback for quick tests.

Add a `db` service using `postgres:17-alpine` with:

- explicitly local development credentials;
- `pg_isready` health checking;
- the shared application network; and
- `postgres-data:/var/lib/postgresql/data`.

Configure the API with `POSTGRES_HOST=db` and make it depend on a healthy
database. The name `db` works through Compose DNS. Do not publish PostgreSQL's
port for the development stack because only other containers require access.

## Part 7 — Apply migrations before container startup

Create executable `backend/entrypoint.sh`:

```sh
#!/usr/bin/env sh
set -eu

python manage.py migrate --noinput
exec "$@"
```

Configure the API image to use it as `ENTRYPOINT`, while retaining the Django
server as `CMD`. `exec` replaces the shell with the server so container stop
signals reach Django correctly.

Extend the container smoke test to execute `showmigrations annotations` and
require `[X] 0001_initial`. Health alone proves the server started; this
assertion proves committed schema history was applied to an empty PostgreSQL
volume. Run the Django test suite inside the API container too, proving the
constraints against PostgreSQL rather than only the SQLite fallback.

## Part 8 — Test against PostgreSQL in CI

Add a PostgreSQL service container to the `repository-validation` CI job. Give
it a health check and expose port 5432 to the job runner. Set the matching
`POSTGRES_*` environment variables at job level.

Django's test runner does not write tests into the configured development
database. It creates a separate test database, runs migrations, executes tests,
and destroys it. This isolation makes repeatable CI possible.

The command remains `make check`; only the CI environment selects PostgreSQL.
Locally, students can use SQLite for the fast gate and the Compose smoke test for
real PostgreSQL integration.

## Part 9 — Verify persistence and constraints

```bash
make check
make container-test
docker compose up --build --detach --wait
docker compose exec api python manage.py showmigrations annotations
docker compose exec db psql --username webann --dbname webann
```

Inside `psql`, `\dt` lists tables and `\d annotations_project` describes the
project table. Exit with `\q`.

Stop without deleting the volume, start again, and observe that data remains:

```bash
docker compose down
docker compose up --detach --wait
```

Delete the lesson database only intentionally:

```bash
docker compose down --volumes
```

## Part 10 — Open the pull request

Run `git diff --check` and `git status --short`. Open a PR titled
`Lesson 5: add PostgreSQL domain model`. Include the initial red tests, final
green results, reviewed migration, ER diagram, deletion-policy reasoning, and
confirmation that CI used PostgreSQL.

## Acceptance criteria

- The five models and documented relationships exist.
- Invalid color/status data fails model validation.
- Database constraints reject every documented duplicate scope.
- Protect and cascade deletion semantics have tests.
- Migration `0001_initial` applies to an empty PostgreSQL database.
- `makemigrations --check --dry-run` reports no drift.
- CI tests use an isolated PostgreSQL test database.
- Compose waits for database health and persists local data in a named volume.
- The smoke test verifies the initial migration was applied.
- All local and container quality gates pass.

## Gold-standard implementation

Read this after your implementation and first PR review. The instructor
publishes the reference checkpoint as `lesson-05`.

```bash
git fetch --tags
git diff lesson-05 -- . ':!docs/lessons/05-POSTGRES-DOMAIN-MODEL.md'
```

The gold implementation maps relationships to foreign keys, flexible metadata
to JSON, scoped identity to named database constraints, and lifecycle ownership
to protect/cascade policies. Builders keep tests readable; migrations are
generated and reviewed; local fast tests can use SQLite while CI and Compose
exercise PostgreSQL. The API waits for database health and applies migrations
before serving traffic.

Different helper names are acceptable. A gold-standard solution preserves the
same domain invariants at the correct layer and proves them through tests—not
only comments or form validation.

## What you should now be able to explain

- model state versus database schema versus migration history;
- foreign key and reverse relationship;
- global versus scoped uniqueness;
- validation error versus database integrity error;
- `CASCADE` versus `PROTECT`;
- why `transaction.atomic()` matters around expected integrity failures;
- JSON metadata versus relational entities;
- database health versus process startup; and
- how Django creates an isolated test database.
