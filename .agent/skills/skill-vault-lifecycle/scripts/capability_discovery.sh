#!/usr/bin/env bash
set -e

# Grounds the agent in the actual binary version and capabilities
if ! command -v vault &> /dev/null; then
    echo "[!] Vault binary missing. Attempting self-healing installation..."
    # Check for brew (assumed available in this dev environment)
    if command -v brew &> /dev/null; then
        brew tap hashicorp/tap
        brew install hashicorp/tap/vault
    else
        echo "[ERROR] Homebrew not found. Manual installation required."
        exit 1
    fi
fi

VERSION=$(vault --version)
echo "[*] Vault Binary: $VERSION"

echo "[*] Parsing operator init capabilities..."
vault operator init --help | head -n 20 > .capabilities_init.tmp

echo "[*] Parsing operator rekey capabilities..."
vault operator rekey --help | head -n 20 > .capabilities_rekey.tmp

echo "[SUCCESS] Skill grounded in binary at $(which vault)"
