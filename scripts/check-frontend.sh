#!/usr/bin/env bash
set -euo pipefail

repository_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repository_root"

bash scripts/check-node-runtime.sh node

if [[ ! -d frontend/node_modules ]]; then
  echo "ERROR: frontend dependencies are missing. Run: make frontend-bootstrap" >&2
  exit 1
fi

npm --prefix frontend run check
echo "Frontend quality checks passed."
