#!/usr/bin/env bash
# Local build only. No AWS login, upload, resource creation or model call.
set -euo pipefail
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_BIN="${PYTHON_BIN:-python3}"
BUILD_DIR="${1:-${PROJECT_DIR}/.lambda}"
mkdir -p "$BUILD_DIR"
BUILD_DIR="$(cd "$BUILD_DIR" && pwd)"

cd "$PROJECT_DIR"
npm ci --no-audit --no-fund
npm run build

STAGE_DIR="$(mktemp -d "${BUILD_DIR}/stage.XXXXXX")"
trap 'rm -rf "$STAGE_DIR"' EXIT

# Lambda Python 3.13 uses Amazon Linux 2023 (glibc 2.34). These binary-wheel
# platforms work there; macOS binaries must never enter the deployment ZIP.
"$PYTHON_BIN" -m pip install \
  --platform manylinux2014_aarch64 \
  --platform manylinux_2_28_aarch64 \
  --platform manylinux_2_34_aarch64 \
  --implementation cp --python-version 3.13 \
  --abi cp313 --abi abi3 --abi none \
  --only-binary=:all: --no-compile \
  --target "$STAGE_DIR" \
  -r "$PROJECT_DIR/infra/requirements-lambda.txt"

"$PYTHON_BIN" "$PROJECT_DIR/scripts/verify_aws_package.py" \
  "$PROJECT_DIR" "$STAGE_DIR" "$BUILD_DIR"
