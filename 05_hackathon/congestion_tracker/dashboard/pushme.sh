#!/bin/bash
# pushme.sh

# Push the Shiny dashboard app to Posit Connect (Option 1: API is deployed separately).

# Install rsconnect package for Python
python -m pip install --upgrade pip
python -m pip install rsconnect-python

# This script expects CONNECT_SERVER and CONNECT_API_KEY to be set in your shell env.
# Example:
#   export CONNECT_SERVER="https://connect.example.edu"
#   export CONNECT_API_KEY="YOUR_KEY"
if [[ -z "${CONNECT_SERVER:-}" || -z "${CONNECT_API_KEY:-}" ]]; then
  echo "Missing CONNECT_SERVER or CONNECT_API_KEY in environment."
  exit 1
fi

# Resolve repo root and app dir reliably (script can be run from anywhere)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP_DIR="${SCRIPT_DIR}"

# Deploy the dashboard (requires manifest.json in the dashboard folder)
rsconnect deploy shiny \
  --server "${CONNECT_SERVER}" \
  --api-key "${CONNECT_API_KEY}" \
  "${APP_DIR}"