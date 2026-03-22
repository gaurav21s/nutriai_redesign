#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$ROOT_DIR/backend"
FRONTEND_DIR="$ROOT_DIR/frontend"
SPAWNER="$ROOT_DIR/scripts/spawn_daemon.py"

RUNTIME_DIR="$ROOT_DIR/.runtime"
LOG_DIR="$ROOT_DIR/logs"
mkdir -p "$RUNTIME_DIR" "$LOG_DIR"

BACKEND_PID_FILE="$RUNTIME_DIR/backend.pid"
FRONTEND_PID_FILE="$RUNTIME_DIR/frontend.pid"

BACKEND_LOG="$LOG_DIR/backend.log"
FRONTEND_LOG="$LOG_DIR/frontend.log"

BACKEND_HOST="${BACKEND_HOST:-127.0.0.1}"
BACKEND_PORT="${BACKEND_PORT:-8008}"
FRONTEND_HOST="${FRONTEND_HOST:-127.0.0.1}"
FRONTEND_PORT="${FRONTEND_PORT:-3005}"
FRONTEND_CLEAN_CACHE="${FRONTEND_CLEAN_CACHE:-1}"
RESET_LOGS_ON_START="${RESET_LOGS_ON_START:-1}"

if [[ "$RESET_LOGS_ON_START" == "1" ]]; then
  : >"$BACKEND_LOG"
  : >"$FRONTEND_LOG"
fi

is_running() {
  local pid="$1"
  kill -0 "$pid" >/dev/null 2>&1
}

listener_pid_for_port() {
  local port="$1"
  if ! command -v lsof >/dev/null 2>&1; then
    return
  fi
  lsof -ti tcp:"$port" -sTCP:LISTEN 2>/dev/null | head -n 1
}

kill_port_processes() {
  local port="$1"
  if ! command -v lsof >/dev/null 2>&1; then
    return
  fi

  local pids
  pids="$(lsof -ti tcp:"$port" 2>/dev/null || true)"
  if [[ -z "${pids:-}" ]]; then
    return
  fi

  echo "Cleaning port $port: $pids"
  for pid in $pids; do
    if ! kill "$pid" >/dev/null 2>&1; then
      echo "Could not stop PID $pid with TERM"
    fi
  done
  sleep 0.4
  for pid in $pids; do
    if kill -0 "$pid" >/dev/null 2>&1; then
      if ! kill -9 "$pid" >/dev/null 2>&1; then
        echo "Could not force stop PID $pid"
      fi
    fi
  done
}

stop_if_started() {
  if [[ -f "$BACKEND_PID_FILE" ]]; then
    local pid
    pid="$(cat "$BACKEND_PID_FILE" || true)"
    if [[ -n "${pid:-}" ]] && is_running "$pid"; then
      kill "$pid" >/dev/null 2>&1 || true
    fi
    rm -f "$BACKEND_PID_FILE"
  fi
  if [[ -f "$FRONTEND_PID_FILE" ]]; then
    local pid
    pid="$(cat "$FRONTEND_PID_FILE" || true)"
    if [[ -n "${pid:-}" ]] && is_running "$pid"; then
      kill "$pid" >/dev/null 2>&1 || true
    fi
    rm -f "$FRONTEND_PID_FILE"
  fi
}

start_backend() {
  kill_port_processes "$BACKEND_PORT"

  if [[ ! -x "$BACKEND_DIR/.venv/bin/python" ]]; then
    echo "Backend Python not found at $BACKEND_DIR/.venv/bin/python"
    exit 1
  fi

  if [[ -f "$BACKEND_PID_FILE" ]]; then
    local existing
    existing="$(cat "$BACKEND_PID_FILE" || true)"
    if [[ -n "${existing:-}" ]] && is_running "$existing"; then
      echo "Backend already running (PID $existing)"
      return
    fi
    rm -f "$BACKEND_PID_FILE"
  fi

  (
    cd "$ROOT_DIR"
    "$BACKEND_DIR/.venv/bin/python" "$SPAWNER" \
      "$BACKEND_DIR" \
      "$BACKEND_LOG" \
      "$BACKEND_PID_FILE" \
      "$BACKEND_DIR/.venv/bin/python" -m uvicorn app.main:app --host "$BACKEND_HOST" --port "$BACKEND_PORT"
  )

  sleep 1
  local pid
  pid="$(cat "$BACKEND_PID_FILE")"
  if ! is_running "$pid"; then
    echo "Backend failed to start. Recent log output:"
    tail -n 60 "$BACKEND_LOG" || true
    stop_if_started
    exit 1
  fi

  local health_host="$BACKEND_HOST"
  if [[ "$health_host" == "0.0.0.0" ]]; then
    health_host="127.0.0.1"
  fi

  local ready="0"
  for _ in {1..20}; do
    if curl --max-time 2 -fsS "http://$health_host:$BACKEND_PORT/api/v1/health" >/dev/null 2>&1; then
      ready="1"
      break
    fi
    sleep 0.4
  done

  if [[ "$ready" != "1" ]]; then
    echo "Backend failed health check at http://$health_host:$BACKEND_PORT/api/v1/health"
    echo "Recent backend logs:"
    tail -n 80 "$BACKEND_LOG" || true
    stop_if_started
    exit 1
  fi

  local listener_pid
  listener_pid="$(listener_pid_for_port "$BACKEND_PORT" || true)"
  if [[ -n "${listener_pid:-}" ]]; then
    echo "$listener_pid" >"$BACKEND_PID_FILE"
    pid="$listener_pid"
  fi

  echo "Backend started (PID $pid) at http://$BACKEND_HOST:$BACKEND_PORT"
}

start_frontend() {
  kill_port_processes "$FRONTEND_PORT"

  if ! command -v npm >/dev/null 2>&1; then
    echo "npm is not available in PATH."
    stop_if_started
    exit 1
  fi

  if [[ ! -x "$FRONTEND_DIR/node_modules/.bin/next" ]]; then
    echo "Next.js binary not found at $FRONTEND_DIR/node_modules/.bin/next"
    stop_if_started
    exit 1
  fi

  if [[ -f "$FRONTEND_PID_FILE" ]]; then
    local existing
    existing="$(cat "$FRONTEND_PID_FILE" || true)"
    if [[ -n "${existing:-}" ]] && is_running "$existing"; then
      echo "Frontend already running (PID $existing)"
      return
    fi
    rm -f "$FRONTEND_PID_FILE"
  fi

  if [[ "$FRONTEND_CLEAN_CACHE" == "1" ]]; then
    rm -rf "$FRONTEND_DIR/.next"
  fi

  (
    cd "$FRONTEND_DIR"
    ./node_modules/.bin/next build >>"$FRONTEND_LOG" 2>&1
  )

  (
    cd "$ROOT_DIR"
    "$BACKEND_DIR/.venv/bin/python" "$SPAWNER" \
      "$FRONTEND_DIR" \
      "$FRONTEND_LOG" \
      "$FRONTEND_PID_FILE" \
      "$FRONTEND_DIR/node_modules/.bin/next" start --hostname "$FRONTEND_HOST" --port "$FRONTEND_PORT"
  )

  sleep 1
  local pid
  pid="$(cat "$FRONTEND_PID_FILE")"
  if ! is_running "$pid"; then
    echo "Frontend failed to start. Recent log output:"
    tail -n 80 "$FRONTEND_LOG" || true
    stop_if_started
    exit 1
  fi

  local health_host="$FRONTEND_HOST"
  if [[ "$health_host" == "0.0.0.0" ]]; then
    health_host="127.0.0.1"
  fi

  local ready="0"
  local health_url="http://$health_host:$FRONTEND_PORT/api/health"
  for _ in {1..30}; do
    if ! is_running "$pid"; then
      break
    fi
    if curl --max-time 5 -fsS "$health_url" >/dev/null 2>&1; then
      ready="1"
      break
    fi
    sleep 0.5
  done

  if [[ "$ready" != "1" ]]; then
    echo "Frontend failed health check at $health_url"
    echo "Recent frontend logs:"
    tail -n 120 "$FRONTEND_LOG" || true
    stop_if_started
    exit 1
  fi

  local listener_pid
  listener_pid="$(listener_pid_for_port "$FRONTEND_PORT" || true)"
  if [[ -n "${listener_pid:-}" ]]; then
    echo "$listener_pid" >"$FRONTEND_PID_FILE"
    pid="$listener_pid"
  fi

  echo "Frontend started (PID $pid) at http://$FRONTEND_HOST:$FRONTEND_PORT"
}

start_backend
start_frontend

echo ""
echo "Run './stop.sh' to stop both services."
echo "Logs:"
echo "  Backend : $BACKEND_LOG"
echo "  Frontend: $FRONTEND_LOG"
