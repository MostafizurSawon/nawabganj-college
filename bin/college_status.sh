#!/usr/bin/env bash
# Safe, read-only status for the College app (Gunicorn)
set -u

APP_ROOT="/home/jshop/cms.nawabganjcitycollege.edu.bd/college_core"
VENV="$APP_ROOT/venv/bin"
PIDF="$APP_ROOT/run/gunicorn.pid"
PORT="30004"
ERRLOG="$APP_ROOT/run/gunicorn.error.log"
ACCLOG="$APP_ROOT/run/gunicorn.access.log"

ts() { date +"%Y-%m-%d %H:%M:%S %Z"; }
line() { printf '%*s\n' "${COLUMNS:-80}" '' | tr ' ' '-'; }

echo "== College Status @ $(ts) =="
line

# Uptime & Load
UP=$(uptime)
CORES=$(nproc 2>/dev/null || echo "?")
echo "[Uptime/Load]"
echo "$UP"
echo "CPU cores: $CORES"
line

# Listener on PORT
echo "[Port $PORT listeners]"
ss -lptn "sport = :$PORT" || true
line

# Master & Workers
if [[ -s "$PIDF" ]]; then
  MPID=$(cat "$PIDF")
  echo "[Gunicorn Master]"
  ps -fp "$MPID" || echo "Master PID $MPID not found"
  echo
  echo "[Gunicorn Workers (children of $MPID)]"
  pgrep -P "$MPID" >/dev/null 2>&1 && pgrep -P "$MPID" -a | awk '{print $1}' | xargs -r ps -o pid,%cpu,%mem,etime,cmd -fp || echo "No worker children seen"
else
  echo "[Gunicorn]"
  echo "PID file missing or empty: $PIDF"
fi
line

# Resource snapshot (user=jshop + overall memory)
echo "[Top resource usage (user=jshop)]"
ps -u jshop -o pid,%cpu,%mem,etime,cmd --sort=-%cpu | head -n 12
echo
echo "[Memory]"
free -m
line

# Quick access/error log tails
echo "[Last 15 error log lines]"
tail -n 15 "$ERRLOG" 2>/dev/null || echo "No error log at $ERRLOG"
echo
echo "[Last 15 access log lines]"
tail -n 15 "$ACCLOG" 2>/dev/null || echo "No access log at $ACCLOG"
line

# Simple per-minute request estimate (if access log common format)
MIN=$(date +'%d/%b/%Y:%H:%M')
if [[ -f "$ACCLOG" ]]; then
  RPS=$(grep -c "$MIN" "$ACCLOG" 2>/dev/null || echo 0)
  echo "[Requests in current minute (rough): $RPS]"
else
  echo "[Requests in current minute: n/a]"
fi
line

echo "Done."
