#!/usr/bin/env bash
set -e

cleanup() {
  kill "$frontend_pid" "$backend_pid" 2>/dev/null
  wait "$frontend_pid" "$backend_pid" 2>/dev/null
}
trap cleanup EXIT INT TERM

cd "$(dirname "$0")"

(cd agent && uv run cooking_agent) &
backend_pid=$!

(cd web && pnpm run dev) &
frontend_pid=$!

wait
