#!/usr/bin/env bash
set -euo pipefail

project_name="webann_tutorial_smoke"
export API_PORT="${API_PORT:-18080}"
export FRONTEND_PORT="${FRONTEND_PORT:-15173}"
compose=(docker compose --project-name "$project_name")

cleanup() {
  "${compose[@]}" down --volumes --remove-orphans
}

trap cleanup EXIT

assert_response_contains() {
  local description="$1"
  local url="$2"
  local expected="$3"
  local response

  if ! response="$(curl --fail --silent --show-error "$url")"; then
    echo "FAIL: $description did not return a successful HTTP response." >&2
    return 1
  fi

  if [[ "$response" != *"$expected"* ]]; then
    echo "FAIL: $description did not contain: $expected" >&2
    echo "Response: $response" >&2
    return 1
  fi

  echo "PASS: $description"
}

assert_http_status() {
  local description="$1"
  local url="$2"
  local expected="$3"
  local actual

  shift 3

  actual="$(curl --silent --output /dev/null --write-out '%{http_code}' "$@" "$url")"
  if [[ "$actual" != "$expected" ]]; then
    echo "FAIL: $description returned HTTP $actual; expected $expected." >&2
    return 1
  fi

  echo "PASS: $description"
}

"${compose[@]}" config --quiet
"${compose[@]}" build
"${compose[@]}" up --detach --wait

assert_response_contains "API health check" "http://localhost:${API_PORT}/health/" '"status": "ok"'
assert_response_contains "frontend health check" "http://localhost:${FRONTEND_PORT}/health/" '"status":"ok"'
assert_response_contains "service-to-service request" "http://localhost:${FRONTEND_PORT}/api-health/" '"service": "api"'
assert_http_status "anonymous API access is rejected" "http://localhost:${API_PORT}/api/templates/" "401"
assert_http_status "frontend API proxy rejects anonymous access" "http://localhost:${FRONTEND_PORT}/api/auth/me/" "401"
assert_http_status "frontend proxy forwards JSON login requests" \
  "http://localhost:${FRONTEND_PORT}/api/auth/login/" "400" \
  --request POST --header "Content-Type: application/json" \
  --data '{"username":"missing-user","password":"wrong"}'

migrations="$("${compose[@]}" exec --no-TTY api python manage.py showmigrations annotations)"
if [[ "$migrations" != *"[X] 0001_initial"* || "$migrations" != *"[X] 0002_usersecurity"* || "$migrations" != *"[X] 0003_annotationjob_annotationworkitem_annotationresult_and_more"* ]]; then
  echo "FAIL: the annotations migrations were not applied." >&2
  echo "$migrations" >&2
  exit 1
fi
echo "PASS: annotations migrations"

"${compose[@]}" exec --no-TTY api python manage.py test annotations
echo "PASS: Django tests against PostgreSQL"

echo "Container smoke tests passed."
