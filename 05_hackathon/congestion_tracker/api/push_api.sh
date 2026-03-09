#!/bin/bash
# push_api.sh
#
# Push the FastAPI API to Posit Connect (Option 1: dashboard is deployed separately).

python -m pip install --upgrade pip
python -m pip install rsconnect-python

# This script expects CONNECT_SERVER and CONNECT_API_KEY to be set in your shell env.
if [[ -z "${CONNECT_SERVER:-}" || -z "${CONNECT_API_KEY:-}" ]]; then
  echo "Missing CONNECT_SERVER or CONNECT_API_KEY in environment."
  exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
API_DIR="${SCRIPT_DIR}"

# Generate/update manifest (FastAPI entrypoint is fastapi_app:app)
rsconnect write-manifest api --entrypoint fastapi_app:app "${API_DIR}"

# Deploy the API
rsconnect deploy fastapi \
  --server "${CONNECT_SERVER}" \
  --api-key "${CONNECT_API_KEY}" \
  --entrypoint fastapi_app:app \
  "${API_DIR}"

