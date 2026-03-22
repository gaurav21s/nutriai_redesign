#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RUNTIME_DIR="$ROOT_DIR/.runtime"

BACKEND_PID_FILE="$RUNTIME_DIR/backend.pid"
FRONTEND_PID_FILE="$RUNTIME_DIR/frontend.pid"

is_running() {
  local pid="$1"
  kill -0 "$pid" >/dev/null 2>&1
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

stop_pid_file() {
  local name="$1"
  local file="$2"

  if [[ ! -f "$file" ]]; then
    echo "$name: no PID file."
    return
  fi

  local pid
  pid="$(cat "$file" || true)"
  if [[ -z "${pid:-}" ]]; then
    echo "$name: PID file was empty."
    rm -f "$file"
    return
  fi

  if ! is_running "$pid"; then
    echo "$name: process $pid not running."
    rm -f "$file"
    return
  fi

  echo "$name: stopping PID $pid..."
  kill "$pid" >/dev/null 2>&1 || true

  for _ in {1..20}; do
    if ! is_running "$pid"; then
      break
    fi
    sleep 0.25
  done

  if is_running "$pid"; then
    echo "$name: force killing PID $pid..."
    kill -9 "$pid" >/dev/null 2>&1 || true
  fi

  rm -f "$file"
  echo "$name: stopped."
}

stop_pid_file "Frontend" "$FRONTEND_PID_FILE"
stop_pid_file "Backend" "$BACKEND_PID_FILE"

kill_port_processes 3005
kill_port_processes 8008
