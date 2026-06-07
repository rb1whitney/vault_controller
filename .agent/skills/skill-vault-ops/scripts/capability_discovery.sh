#!/usr/bin/env bash
set -e

# Grounds the agent in the actual binary version and operational capabilities
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

echo "[*] Parsing operator raft capabilities..."
vault operator raft --help | head -n 20 > .capabilities_raft.tmp

echo "[*] Parsing status capabilities..."
vault status --help | head -n 20 > .capabilities_status.tmp

echo "[SUCCESS] Ops skill grounded in binary."
