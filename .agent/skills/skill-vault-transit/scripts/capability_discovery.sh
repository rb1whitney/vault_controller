#!/usr/bin/env bash
set -e

# Grounds the agent in the actual binary version and transit capabilities
if ! command -v vault &> /dev/null; then
    echo "[!] Vault binary missing. Attempting self-healing installation..."
    if command -v brew &> /dev/null; then
        brew tap hashicorp/tap
        brew install hashicorp/tap/vault
    else
        exit 1
    fi
fi

VERSION=$(vault --version)
echo "[*] Vault Binary: $VERSION"

echo "[*] Parsing transit engine capabilities..."
# Mount transit if not present for help parsing
vault write -help transit/keys/example | head -n 20 > .capabilities_transit.tmp

echo "[SUCCESS] Transit skill grounded in binary."
