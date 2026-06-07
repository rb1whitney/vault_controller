#!/usr/bin/env bash
set -e

# Grounds the agent in the linter binaries and their configuration
if ! command -v ruff &> /dev/null; then
    echo "[!] ruff missing. Attempting self-healing installation..."
    pip install ruff
fi

if ! command -v markdownlint &> /dev/null; then
    echo "[!] markdownlint missing. Attempting self-healing installation..."
    if command -v npm &> /dev/null; then
        npm install -g markdownlint-cli
    else
        echo "[ERROR] npm not found."
    fi
fi

echo "[*] Ruff Version: $(ruff --version)"
echo "[*] Markdownlint Version: $(markdownlint --version)"

echo "[*] Parsing ruff check capabilities..."
ruff check --help | head -n 20 > .capabilities_ruff.tmp

echo "[SUCCESS] Review Suite skill grounded in linter binaries."
