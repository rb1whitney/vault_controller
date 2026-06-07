#!/usr/bin/env bash
set -e

# Grounds the agent in the GitHub CLI PR capabilities
if ! command -v gh &> /dev/null; then
    echo "[!] GitHub CLI (gh) missing."
    exit 1
fi

echo "[*] Parsing gh pr capabilities..."
gh pr --help | head -n 20 > .capabilities_pr.tmp

echo "[*] Parsing gh status capabilities..."
gh status --help | head -n 20 > .capabilities_status.tmp

echo "[SUCCESS] PR Creator skill grounded in gh binary."
