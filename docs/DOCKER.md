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

## Apply source changes

Lesson 3 images copy source during `docker build`. Rebuild and replace services
after changing `backend/server.py` or `frontend/server.mjs`:

```bash
docker compose up --build --detach --wait
```

Later development configurations will add faster reload loops where useful.

## Stop the stack

```bash
docker compose down
```

This removes containers and the Compose network but preserves `api-data`.
Delete the volume only when intentionally discarding its local lesson data:

```bash
docker compose down --volumes
```

## Quality and smoke tests

```bash
make check
make container-test
```

The smoke test uses a separate Compose project name and always removes its test
containers, network, and volume. It does not delete the normal development
stack's `api-data` volume.

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
