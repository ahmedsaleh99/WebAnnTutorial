#!/usr/bin/env bash
set -euo pipefail

node_command="${1:-node}"

if ! command -v "$node_command" >/dev/null 2>&1; then
  echo "ERROR: Node.js command not found: $node_command" >&2
  echo "Install or activate Node.js 22; see docs/TOOLING.md" >&2
  exit 1
fi

major_version="$($node_command --version | sed -E 's/^v([0-9]+).*/\1/')"
if [[ "$major_version" != "22" ]]; then
  echo "ERROR: Node.js 22 is required, but $($node_command --version) is active." >&2
  echo "Install or activate Node.js 22; see docs/TOOLING.md" >&2
  exit 1
fi

echo "Node.js runtime check passed: $($node_command --version)"
