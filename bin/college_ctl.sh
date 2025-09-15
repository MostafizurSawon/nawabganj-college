#!/usr/bin/env bash
set -euo pipefail

APP_ROOT="/home/jshop/cms.nawabganjcitycollege.edu.bd/college_core"
VENV="$APP_ROOT/venv/bin"
PID="$APP_ROOT/run/gunicorn.pid"
PORT="30004"
WSGI="config.wsgi:application"
ERRLOG="$APP_ROOT/run/gunicorn.error.log"
ACCLOG="$APP_ROOT/run/gunicorn.access.log"
BIND="0.0.0.0:$PORT"

start_app() {
  mkdir -p "$APP_ROOT/run"
  "$VENV/gunicorn" \
    --chdir "$APP_ROOT" \
    --workers 3 \
    --bind "$BIND" \
    --pid "$PID" \
    --error-logfile "$ERRLOG" \
    --access-logfile "$ACCLOG" \
    --capture-output \
    --daemon \
    "$WSGI"

  for _ in {1..20}; do [ -s "$PID" ] && break; sleep 0.2; done
  if [ ! -s "$PID" ]; then
    MPID="$(ps -eo pid,ppid,cmd | awk -v root="$APP_ROOT" -v v="$VENV" '$3 ~ v"/gunicorn" && $2==1 && $0 ~ root {print $1; exit}')"
    [ -n "${MPID:-}" ] && echo "$MPID" > "$PID"
  fi
}

case "${1:-}" in
  restart)
    echo ">>> Stopping old server..."
    kill -QUIT "$(cat "$PID" 2>/dev/null)" 2>/dev/null || true
    sleep 2
    pkill -f "^$VENV/gunicorn .* --chdir $APP_ROOT" 2>/dev/null || true
    fuser -k -n tcp "$PORT" 2>/dev/null || true
    rm -f "$PID"

    echo ">>> Starting new server..."
    start_app

    [ -s "$PID" ] && echo ">>> Done. Master PID: $(cat "$PID")" || echo ">>> Started, but PID file missing"
    ;;
  status)
    echo ">>> Status on $PORT"
    ss -lptn "sport = :$PORT" || true
    if [ -s "$PID" ]; then
      ps -fp "$(cat "$PID")" || true
    else
      echo "Not running"
    fi
    ;;
  *)
    echo "Usage: $0 {restart|status}"
    ;;
esac
