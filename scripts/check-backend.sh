#!/usr/bin/env bash
set -euo pipefail

repository_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repository_root"

python="$repository_root/.venv/bin/python"
ruff="$repository_root/.venv/bin/ruff"

if [[ ! -x "$python" || ! -x "$ruff" ]]; then
  echo "ERROR: backend tools are missing. Run: make bootstrap" >&2
  exit 1
fi

export DJANGO_SECRET_KEY="test-only-not-a-production-secret"
export DJANGO_DEBUG="false"

"$ruff" format --check backend
"$ruff" check backend
"$python" backend/manage.py check
"$python" backend/manage.py makemigrations --check --dry-run
"$python" backend/manage.py test annotations

echo "Backend quality checks passed."
