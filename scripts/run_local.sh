#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
: "${HEATSHIFT_AGENT_PROVIDER:=ollama}"
: "${HEATSHIFT_AGENT_MODEL:=qwen3:1.7b}"
export HEATSHIFT_AGENT_PROVIDER HEATSHIFT_AGENT_MODEL
python3 -m uvicorn backend.app:app --host 127.0.0.1 --port 8000
