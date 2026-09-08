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

"${compose[@]}" config --quiet
"${compose[@]}" build
"${compose[@]}" up --detach --wait

assert_response_contains "API health check" "http://localhost:${API_PORT}/health/" '"status": "ok"'
assert_response_contains "frontend health check" "http://localhost:${FRONTEND_PORT}/health/" '"status":"ok"'
assert_response_contains "service-to-service request" "http://localhost:${FRONTEND_PORT}/api-health/" '"service": "api"'
assert_response_contains "first persisted visit" "http://localhost:${API_PORT}/visits/" '"visits": 1'

"${compose[@]}" restart api
"${compose[@]}" up --detach --wait

assert_response_contains "visit after API restart" "http://localhost:${API_PORT}/visits/" '"visits": 2'

echo "Container smoke tests passed."
