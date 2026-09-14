# Docker development

## Requirements

- Docker Engine 28 or a compatible current release
- Docker Compose v2 (`docker compose`, not legacy `docker-compose`)
- `curl`

Verify the tools:

```bash
docker --version
docker compose version
docker run --rm hello-world
```

Docker Desktop provides Engine and Compose on macOS and Windows. Linux users
can install Docker Engine and the Compose plugin from Docker's official
instructions. Windows students should enable Docker Desktop's WSL integration
and run course commands inside WSL.

## Start and inspect the stack

```bash
docker compose up --build --detach --wait
docker compose ps
docker compose logs
```

Open:

- frontend: <http://localhost:5173/>
- frontend health: <http://localhost:5173/health/>
- API health: <http://localhost:8000/health/>
- frontend-to-API network check: <http://localhost:5173/api-health/>

The `db` service is PostgreSQL. It is private to the Compose network and stores
data in the `postgres-data` named volume. The API waits for PostgreSQL to become
healthy, then its entrypoint applies committed migrations before Django starts.

## Apply source changes

The images copy source during `docker build`. Rebuild and replace services
after changing Django backend code or `frontend/server.mjs`:

```bash
docker compose up --build --detach --wait
```

Later development configurations will add faster reload loops where useful.

## Stop the stack

```bash
docker compose down
```

This removes containers and the Compose network but preserves PostgreSQL data.
To deliberately reset the local database, add `--volumes`:

```bash
docker compose down --volumes
```

Inspect migration state or open PostgreSQL's shell:

```bash
docker compose exec api python manage.py showmigrations
docker compose exec db psql --username webann --dbname webann
```

## Quality and smoke tests

```bash
make check
make container-test
```

### What a smoke test is

A smoke test is a small, broad test of an assembled system. Its name comes from
the hardware question “does it produce smoke when switched on?” It does not try
to prove every behavior. It answers whether the most important components can
start and communicate in the environment that will run them.

For this repository, `make container-test` proves that:

```text
Dockerfiles build
    ↓
PostgreSQL becomes healthy
    ↓
Django connects and applies migrations
    ↓
the API and frontend become healthy
    ↓
the host can reach both published ports
    ↓
the frontend can reach the API through Compose DNS
    ↓
a representative DRF endpoint returns its pagination contract
    ↓
Django tests pass against PostgreSQL
```

This catches integration failures that a Python test alone cannot detect, such
as a missing image dependency, incorrect command, wrong environment variable,
unapplied migration, invalid health check, incorrect port, broken service name,
or container permission problem.

### What the script does

`scripts/test-containers.sh` performs these steps in order:

1. Enables strict Bash behavior with `set -euo pipefail`, so failed commands,
   unset variables, and failed pipelines stop the test.
2. Selects the isolated Compose project name `webann_tutorial_smoke`.
3. Uses host ports 18080 and 15173 by default to avoid the normal development
   ports 8000 and 5173.
4. Registers an `EXIT` trap before starting anything. Success, failure, or an
   interruption therefore triggers cleanup.
5. Runs `docker compose config --quiet` to reject an invalid Compose model.
6. Builds the real backend and frontend images.
7. Starts services with `--wait`; Compose waits for declared health checks
   rather than relying on a fixed sleep.
8. Calls the API and frontend health endpoints from the host.
9. Calls the frontend's API-health endpoint, proving that the frontend container
   resolves `api` and communicates across the internal network.
10. Calls `/api/templates/` and checks for an empty `results` array, proving one
    representative database-backed DRF route works in the assembled image.
11. Runs `showmigrations` inside the API and verifies `0001_initial` is applied.
12. Runs the Django suite inside the API container, where Django creates an
    isolated PostgreSQL test database and removes it afterward.
13. Runs `docker compose down --volumes --remove-orphans` through the trap,
    removing test containers, network, and data even when an assertion fails.

The script prints a named `PASS` or `FAIL` message for each HTTP assertion and
prints an unexpected response when its content is wrong. This makes CI failures
diagnosable without rerunning them locally.

### Why only one representative CRUD endpoint is curled

The smoke script requests `/api/templates/`, but it does not recreate every API
scenario using shell commands. The Django API tests already cover templates,
projects, dimensions, labels, subjects, validation, filtering, status codes,
and deletion behavior. Those tests also run inside the container against
PostgreSQL.

The template list is a useful representative because it requires no fixture
data while still crossing routing, the DRF router, a ViewSet, serializer,
pagination, ORM, PostgreSQL connection, and JSON rendering. Repeating every
endpoint in Bash would duplicate more precise API tests and make failures harder
to understand.

Use this test-layer division:

| Layer | Main responsibility | Expected characteristics |
| --- | --- | --- |
| Model/unit test | One rule or function | Fast, focused, many cases |
| API test | HTTP contract and validation | Precise setup and assertions |
| Container smoke test | Packaging and service wiring | Few representative paths |
| End-to-end browser test | Critical user journey | Fewest, slowest, highest scope |

### Smoke-test best practices

- Test a deployed-shaped artifact: build the same Dockerfiles used elsewhere.
- Keep the test deterministic; do not depend on data from a developer's normal
  stack or on execution order.
- Isolate names, host ports, databases, and volumes so tests can coexist with
  local development.
- Register cleanup before creating resources, and clean up on both success and
  failure.
- Wait on health/readiness conditions; fixed `sleep 10` calls are both slow and
  unreliable.
- Check behavior, not only whether a process exists. A running Django process
  can still have broken routing or database access.
- Use representative, high-value paths rather than duplicating the entire test
  suite.
- Produce messages that identify which boundary failed and show unexpected
  output without printing secrets.
- Keep credentials obviously test-only and scoped to the disposable stack.
- Make the command safe to rerun and return a nonzero exit code on failure.
- Run the same command locally and in CI: `make container-test`.
- Keep the gate reasonably fast. As the suite grows, separate the quick smoke
  assertions from a longer PostgreSQL integration job rather than allowing a
  “smoke” test to become an unbounded end-to-end suite.

### What a passing smoke test does not prove

A green smoke test does not prove that every input is validated, every role is
authorized, every browser interaction works, performance is acceptable, or
production deployment is correctly configured. Those concerns require focused
API, security, UI, load, and deployment tests. Smoke testing complements those
layers; it does not replace them.

## Troubleshooting

- **Cannot connect to the Docker daemon:** start Docker Desktop or the Docker
  service and verify that your account can use it.
- **Port already allocated:** stop the process or Compose project already using
  ports 5173 or 8000, or choose different host ports without changing the
  container ports:

  ```bash
  API_PORT=18000 FRONTEND_PORT=15173 docker compose up --build --detach --wait
  ```
- **Container is unhealthy:** run `docker compose ps` and
  `docker compose logs SERVICE`.
- **Source change is missing:** rebuild with `docker compose up --build` because
  source is copied into the image.
- **Name resolution:** use service names such as `api` only inside the Compose
  network. From the host, use the published `localhost` port.
