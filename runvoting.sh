#!/usr/bin/env bash
set -euo pipefail

usage() {
  echo "Usage: $0 main|dec25" >&2
  exit 2
}

case "${1:-}" in
  main|dec25) ;;
  *) usage ;;
esac

branch="$1"

# Kill existing screen session with this name (if any)
if screen -ls | grep -q "[.]$branch[[:space:]]"; then
  echo "Stopping existing screen session '$branch'"
  screen -S "$branch" -X quit || true
  # clean up any dead sockets
  screen -wipe >/dev/null 2>&1 || true
fi

# Update remote branch information
if ! git fetch origin; then
  echo "ERROR: git fetch failed; aborting." >&2
  exit 1
fi

# Switch to target branch
if ! git checkout "$branch"; then
  echo "ERROR: git checkout $branch failed; aborting." >&2
  exit 1
fi

if ! git pull --ff-only origin "$branch"; then
  echo "ERROR: could not update $branch; aborting." >&2
  exit 1
fi

lock_file="vue-frontend/package-lock.json"
if [[ -f "$lock_file" ]]; then
  installed_lock="vue-frontend/node_modules/.package-lock.json"
  if [[ ! -f "$installed_lock" ]] || [[ "$lock_file" -nt "$installed_lock" ]]; then
    (cd vue-frontend && npm ci)
  fi
else
  # Historical branches do not track a lockfile.
  (cd vue-frontend && npm install)
fi

# Start a detached screen session that keeps running
if ! screen -dmS "$branch" bash -lc "
  set -e
  cd vue-frontend
  npm run build

  cd ../backend
  uv run --locked python web.py
"; then
  echo "ERROR: failed to start screen session '$branch'." >&2
  exit 1
fi

echo "Screen session '$branch' started and running."
echo "Attach with: screen -r $branch"
