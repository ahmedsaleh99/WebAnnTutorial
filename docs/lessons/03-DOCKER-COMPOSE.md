# Lesson 3 — Docker fundamentals and Compose architecture

## Goal

In this pull request, you will package two deliberately small web services and
run them together with Docker Compose. The services are placeholders: Python's
and Node's standard libraries keep the focus on containers. Django replaces the
Python placeholder in Lesson 4, and React replaces the Node placeholder in
Lesson 9.

By the end, you should be able to explain the difference between an image and a
container, how Compose provides service discovery, why persistent data belongs
in a volume, and how health checks make startup behavior testable.

**Branch:** `lesson/03-docker-compose`

**Prerequisite:** Lesson 2 is merged into `main`, `make check` passes, and Docker
Engine with the Compose plugin is installed. See [Docker reference](../DOCKER.md).

## Deliverables

- minimal backend and frontend HTTP services;
- one Dockerfile and `.dockerignore` per build context;
- a Compose application with health checks, a private network, and a volume;
- local Compose configuration validation;
- an end-to-end container smoke test; and
- a CI job that runs the same smoke test as a developer.

## Part 1 — Start the pull request

Update your local `main`, verify the previous checkpoint, then create the lesson
branch:

```bash
git switch main
git pull --ff-only
make check
git switch -c lesson/03-docker-compose
```

Confirm that `git branch --show-current` prints
`lesson/03-docker-compose`. Do not work directly on `main`.

## Part 2 — Describe the contract first (red)

This infrastructure lesson uses executable repository checks as its first
tests. Add these paths to the required-file list in
`scripts/validate-repository.sh` before creating them:

```text
backend/.dockerignore
backend/Dockerfile
backend/server.py
docker-compose.yml
docs/DOCKER.md
frontend/.dockerignore
frontend/Dockerfile
frontend/server.mjs
scripts/check-compose.sh
scripts/test-containers.sh
```

Also add both new scripts to the validator's executable-file loop. That means
the existing loop that checks executable permissions must now check
`scripts/check-compose.sh` and `scripts/test-containers.sh` too. Run:

```bash
make validate
```

It should fail and name the missing files. This is the **red** result: the
repository contract exists before its implementation. Record that evidence in
the pull request.

## Part 3 — Build the backend image

Create `backend/server.py`, a small Python HTTP server with three behaviors:

- `GET /health/` returns service name `api` and status `ok`;
- `GET /visits/` increments a counter stored in `/data/visits.txt`;
- every other path returns HTTP 404.

The health endpoint proves the process can answer requests. The visits endpoint
exists to demonstrate persistence across a container restart; it is not an
application feature.

Create `backend/Dockerfile` using `python:3.12-slim`. It should:

1. set `/app` as the working directory;
2. create a non-root user;
3. create `/data` and give that user permission to write there;
4. copy only `server.py` into the image;
5. switch to the non-root user;
6. document port 8000 with `EXPOSE`; and
7. start the server with the JSON-array form of `CMD`.

Create `backend/.dockerignore` and exclude Python caches, virtual environments,
test caches, local databases, and environment files.

Important distinctions:

- A **Dockerfile** is a recipe.
- An **image** is the immutable packaged result of building that recipe.
- A **container** is a running instance of an image.
- The **build context** is the directory Docker may read during the build.
- `.dockerignore` keeps irrelevant or sensitive files out of that context.

## Part 4 — Build the frontend image

Create `frontend/server.mjs`, a minimal Node HTTP server with:

- `GET /` returning a placeholder HTML heading;
- `GET /health/` returning service name `frontend` and status `ok`;
- `GET /api-health/` fetching the backend health endpoint; and
- HTTP 404 for unknown paths.

Read the backend URL from `API_URL` and the listening port from `PORT`. Create a
`frontend/Dockerfile` based on `node:22-alpine`, copy the server, run as a
non-root user, expose port 5173, and start it with `node server.mjs`. Add a
matching `.dockerignore` that excludes `node_modules`, build output, coverage,
logs, caches, and environment files.

The Node service is not React. It gives us a second independently built service
so we can learn networking now; React and Vite arrive only after their concepts
are introduced.

## Part 5 — Connect the services with Compose

Create `docker-compose.yml` at the repository root. Define:

- an `api` service built from `./backend`;
- a `frontend` service built from `./frontend`;
- one application network used by both services;
- a named volume mounted at `/data` in the API;
- health checks for both services; and
- `frontend.depends_on.api.condition: service_healthy`.

Publish API container port 8000 and frontend container port 5173. Make the host
ports configurable so CI does not collide with other processes:

```yaml
ports:
  - "${API_PORT:-8000}:8000"
```

Use the same pattern with `FRONTEND_PORT` and 5173.

Compose creates DNS names from service names. Therefore the frontend reaches
the API at `http://api:8000/health/`, not `localhost`. Inside the frontend
container, `localhost` means the frontend container itself. Published ports are
for traffic from the host; containers communicate through their shared network.

The named volume has a different lifecycle from a container. Restarting or
recreating the API container does not erase the visit counter. `docker compose
down --volumes` explicitly removes it.

## Part 6 — Add the fast configuration check (green)

Create executable `scripts/check-compose.sh`. It should:

1. fail clearly if `docker` is unavailable;
2. verify that the Compose plugin is available with `docker compose version`;
3. run `docker compose config --quiet`; and
4. print a success message.

Add `make container-check` and call the script from `scripts/check`. Then run:

```bash
chmod +x scripts/check-compose.sh scripts/test-containers.sh
make check
```

`docker compose config` resolves and validates the Compose model without
building images or starting containers. This makes it appropriate for the fast
local quality gate.

## Part 7 — Run and inspect the application

Build and start the stack:

```bash
docker compose up --build --detach --wait
docker compose ps
docker compose logs
```

Check its behavior:

```bash
curl http://localhost:8000/health/
curl http://localhost:5173/health/
curl http://localhost:5173/api-health/
curl http://localhost:8000/visits/
```

Restart only the API and request `/visits/` again:

```bash
docker compose restart api
docker compose up --detach --wait
curl http://localhost:8000/visits/
```

The counter should increase, demonstrating volume persistence. Inspect with
`docker compose ps` and `docker compose logs api` if a service is unhealthy.
Clean up when finished:

```bash
docker compose down --volumes
```

## Part 8 — Automate the container smoke test

Create executable `scripts/test-containers.sh`. The test should use a unique
Compose project name and alternate host ports, then:

1. validate configuration;
2. build both images;
3. start the stack and wait for health checks;
4. test API health and frontend health;
5. test the frontend-to-API request, proving internal DNS/networking;
6. create the first visit;
7. restart the API;
8. verify that the second visit survives the restart; and
9. always run `down --volumes --remove-orphans` through an `EXIT` trap.

Add `make container-test` as the stable entry point. A good smoke test prints a
specific failure description and the unexpected response, not merely exit code
1. Run it from a clean state:

```bash
make container-test
```

This is an integration test: it crosses process, HTTP, network, filesystem, and
container boundaries. Later lessons will add faster unit tests beneath it.

## Part 9 — Run the smoke test in CI

Add a `container-smoke` job to `.github/workflows/ci.yml`. It needs only these
steps:

1. check out the repository;
2. run `make container-test`.

GitHub-hosted Ubuntu runners already provide Docker Engine and Compose. Keep the
normal repository check and the container smoke test as separate jobs so the
pull request shows which layer failed. The CI workflow must call the same Make
target used locally; do not duplicate its commands in YAML.

## Part 10 — Refactor, document, and open the PR

Run the complete evidence set:

```bash
make check
make container-test
git status --short
git diff --check
```

Open a pull request titled `Lesson 3: add Docker Compose foundation`. In its
description, include:

- the initial missing-file failure;
- successful output from both Make commands;
- what the shared network and named volume do;
- the URLs tested manually; and
- confirmation that no `.env`, generated dependency, or volume data is tracked.

Merge only after required checks pass and the lesson review requirement is met.

## Acceptance criteria

- A clean checkout can build and start both services.
- Both services become healthy.
- The frontend reaches the API using the Compose service name.
- The visit value survives an API container restart.
- Cleanup removes the lesson's containers, network, and test volume.
- `make check` validates the Compose model.
- `make container-test` passes locally and in the separate CI job.
- Images run application processes as a non-root user.
- Runtime secrets and local generated data are not committed.

## Gold-standard implementation

Read this section only after completing your implementation and opening the
pull request.

The reference checkpoint is the repository tag `lesson-03`. Compare it with
your branch:

```bash
git fetch --tags
git diff lesson-03 -- . ':!docs/lessons/03-DOCKER-COMPOSE.md'
```

The gold implementation uses standard-library placeholder servers, non-root
Python 3.12 and Node 22 images, isolated build contexts, one explicit network,
one named data volume, service health checks, configurable host ports, and an
EXIT-trapped smoke test. Its CI invokes the exact local Make target.

Your code need not be textually identical. It is gold-standard when it has the
same observable guarantees, produces useful failures, stays understandable to a
new student, and satisfies every acceptance criterion. Explain intentional
differences in the pull request rather than copying the reference blindly.

## What you should now be able to explain

- image versus container;
- build context and `.dockerignore`;
- container port versus published host port;
- service-name DNS versus `localhost`;
- bind mount versus named volume;
- process startup versus application health;
- `depends_on` with a health condition; and
- configuration validation versus an end-to-end smoke test.
