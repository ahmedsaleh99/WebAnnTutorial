#!/usr/bin/env bash
set -euo pipefail

while IFS= read -r -d '' shell_file; do
  bash -n "$shell_file"
done < <(find scripts -type f -print0)

echo "Shell syntax validation passed."
