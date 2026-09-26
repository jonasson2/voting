#!/usr/bin/env bash
set -euo pipefail

root="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
port=5001

if pids="$(lsof -nP -tiTCP:"$port" -sTCP:LISTEN)" && [[ -n "$pids" ]]; then
  kill $pids
  for _ in {1..20}; do
    if ! lsof -nP -tiTCP:"$port" -sTCP:LISTEN >/dev/null; then
      break
    fi
    sleep 0.2
  done
  if lsof -nP -tiTCP:"$port" -sTCP:LISTEN >/dev/null; then
    echo "Port $port is still occupied." >&2
    exit 1
  fi
fi

(cd "$root/vue-frontend" && npm run build)

mkdir -p "$root/tmp"
screen -S voting-local -X quit >/dev/null 2>&1 || true
screen -dmS voting-local bash -c '
  cd "$1"
  FLASK_RUN_PORT=5001 FLASK_RUN_HOST=127.0.0.1 \
    exec uv run --locked python web.py > "$2" 2>&1
' _ "$root/backend" "$root/tmp/web-$port.log"

for _ in {1..30}; do
  if curl -fsS "http://127.0.0.1:$port/" > /dev/null 2>&1; then
    echo "Simulator running at http://127.0.0.1:$port/"
    exit 0
  fi
  sleep 0.2
done

echo "Server did not start; see $root/tmp/web-$port.log" >&2
exit 1
