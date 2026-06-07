#!/usr/bin/env bash
set -e

# Grounds the agent in the actual binary version and GitHub CLI capabilities
if ! command -v git &> /dev/null; then
    echo "[!] git binary missing."
    exit 1
fi

if ! command -v gh &> /dev/null; then
    echo "[!] GitHub CLI (gh) missing. Attempting self-healing installation..."
    if command -v brew &> /dev/null; then
        brew install gh
    else
        echo "[ERROR] Homebrew not found. Manual installation required."
        exit 1
    fi
fi

GIT_VERSION=$(git --version)
GH_VERSION=$(gh --version | head -n 1)
echo "[*] Git Binary: $GIT_VERSION"
echo "[*] GitHub CLI: $GH_VERSION"

echo "[*] Parsing gh repo capabilities..."
gh repo --help | head -n 20 > .capabilities_repo.tmp

echo "[*] Parsing git hook capabilities..."
git help hook | head -n 20 > .capabilities_hooks.tmp

echo "[SUCCESS] Repo Operations skill grounded in binaries."
