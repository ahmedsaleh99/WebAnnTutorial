#!/usr/bin/env bash
set -euo pipefail

python_command="${1:-python3}"

if ! command -v "$python_command" >/dev/null 2>&1; then
  echo "ERROR: Python command not found: $python_command" >&2
  echo "Install or activate Python 3.12; see docs/TOOLING.md" >&2
  exit 1
fi

"$python_command" - <<'PYTHON'
import sys

required = (3, 12)
actual = sys.version_info[:2]

if actual != required:
    print(
        f"ERROR: Python 3.12 is required, but {sys.version.split()[0]} is active.",
        file=sys.stderr,
    )
    print(
        "Install or activate Python 3.12; see docs/TOOLING.md",
        file=sys.stderr,
    )
    raise SystemExit(1)

print(f"Python runtime check passed: {sys.version.split()[0]}")
PYTHON
