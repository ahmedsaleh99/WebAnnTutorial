#!/usr/bin/env bash
set -euo pipefail

required_files=(
  ".editorconfig"
  ".github/PULL_REQUEST_TEMPLATE.md"
  ".github/dependabot.yml"
  ".github/workflows/cd.yml"
  ".github/workflows/ci.yml"
  ".gitignore"
  ".nvmrc"
  ".pre-commit-config.yaml"
  ".python-version"
  "CONTRIBUTING.md"
  "LICENSE"
  "Makefile"
  "README.md"
  "backend/.dockerignore"
  "backend/Dockerfile"
  "backend/annotations/apps.py"
  "backend/annotations/tests/test_health.py"
  "backend/annotations/urls.py"
  "backend/annotations/views.py"
  "backend/config/settings.py"
  "backend/config/urls.py"
  "backend/config/wsgi.py"
  "backend/manage.py"
  "backend/requirements.txt"
  "docker-compose.yml"
  "docs/BRANCH_PROTECTION.md"
  "docs/DOCKER.md"
  "docs/TOOLING.md"
  "frontend/.dockerignore"
  "frontend/Dockerfile"
  "frontend/server.mjs"
  "pyproject.toml"
  "requirements-dev.txt"
)

failure_count=0

for required_file in "${required_files[@]}"; do
  if [[ ! -f "$required_file" ]]; then
    echo "ERROR: required file is missing: $required_file" >&2
    failure_count=$((failure_count + 1))
  fi
done

for executable_file in \
  scripts/check \
  scripts/check-backend.sh \
  scripts/check-compose.sh \
  scripts/check-python-runtime.sh \
  scripts/check-shell.sh \
  scripts/test-containers.sh \
  scripts/validate-repository.sh; do
  if [[ ! -x "$executable_file" ]]; then
    echo "ERROR: $executable_file must be executable" >&2
    failure_count=$((failure_count + 1))
  fi
done

if [[ -f .python-version ]] && ! grep -qx '3.12' .python-version; then
  echo "ERROR: .python-version must declare Python 3.12" >&2
  failure_count=$((failure_count + 1))
fi

if [[ -f .nvmrc ]] && ! grep -qx '22' .nvmrc; then
  echo "ERROR: .nvmrc must declare Node.js 22" >&2
  failure_count=$((failure_count + 1))
fi

if git grep -nI -E '[[:blank:]]+$' -- ':!*.md'; then
  echo "ERROR: trailing whitespace found outside Markdown files" >&2
  failure_count=$((failure_count + 1))
fi

for forbidden_file in .env db.sqlite3; do
  if git ls-files --error-unmatch "$forbidden_file" >/dev/null 2>&1; then
    echo "ERROR: forbidden local or secret file is tracked: $forbidden_file" >&2
    failure_count=$((failure_count + 1))
  fi
done

if git ls-files | grep -Eq '(^|/)(node_modules|dist|coverage|media|docker-data)/'; then
  echo "ERROR: generated or runtime data is tracked" >&2
  failure_count=$((failure_count + 1))
fi

if [[ "$failure_count" -ne 0 ]]; then
  echo "Repository validation failed with $failure_count error(s)." >&2
  exit 1
fi

echo "Repository validation passed."
