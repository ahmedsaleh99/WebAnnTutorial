#!/usr/bin/env bash
set -euo pipefail

if ! command -v docker >/dev/null 2>&1; then
  echo "ERROR: Docker is required; see docs/DOCKER.md" >&2
  exit 1
fi

docker compose version >/dev/null
docker compose config --quiet

echo "Docker Compose validation passed."
