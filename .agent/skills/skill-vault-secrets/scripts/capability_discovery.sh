#!/usr/bin/env bash
set -e

# Grounds the agent in the actual binary version and auth/secret capabilities
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

echo "[*] Parsing auth capabilities..."
vault auth help | head -n 20 > .capabilities_auth.tmp

echo "[*] Parsing secrets capabilities..."
vault secrets help | head -n 20 > .capabilities_secrets.tmp

echo "[SUCCESS] Secrets skill grounded in binary."
