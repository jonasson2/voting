#!/usr/bin/env bash
set -euo pipefail

usage() {
  echo "Usage: $0 main|dev|dec25" >&2
  exit 2
}

case "${1:-}" in
  main|dev|dec25) ;;
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

# Update repository
if ! git pull; then
  echo "ERROR: git pull failed; aborting." >&2
  exit 1
fi

# Switch to target branch
if ! git checkout "$branch"; then
  echo "ERROR: git checkout $branch failed; aborting." >&2
  exit 1
fi

# Start a detached screen session that keeps running
if ! screen -dmS "$branch" bash -lc "
  set -e
  # make conda available in non-interactive shell
  source \"\$(conda info --base)/etc/profile.d/conda.sh\"
  conda activate voting

  cd vue-frontend
  npm run build

  cd ../backend
  python web.py
"; then
  echo "ERROR: failed to start screen session '$branch'." >&2
  exit 1
fi

echo "Screen session '$branch' started and running."
echo "Attach with: screen -r $branch"
