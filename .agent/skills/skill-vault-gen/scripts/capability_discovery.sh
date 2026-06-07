#!/usr/bin/env bash
set -e

# Grounds the agent in the generation toolchain requirements
echo "[*] Verifying secret generation dependencies..."

# Python for the generator
if ! command -v python3 &> /dev/null; then
    echo "[!] python3 missing."
    exit 1
fi

# Cloud CLIs for specific rules
if ! command -v gcloud &> /dev/null; then
    echo "[WARN] gcloud CLI missing. GCP SA generation will fail."
fi

if ! command -v aws &> /dev/null; then
    echo "[WARN] aws CLI missing. AWS IAM key generation will fail."
fi

echo "[SUCCESS] Generation environment verified."
