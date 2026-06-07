---
name: skill-github
description: Enforces repository hygiene and semantic commit standards for the Vault Controller codebase, including mandatory pre-commit secret scanning. Triggers: vault-commit, secret-scan.
---
# GitHub Repository Authority

## Execution Boundary
You are the master of the "Local State" phase. You ensure that code is semantically packaged and cryptographically safe before it leaves the developer workstation.

## Grounding Protocol
Before git operations:
1. **Sync with Binary**: Run `{SKILL_DIR}/scripts/capability_discovery.sh`. Ensure `gh` is authenticated and `git` is configured.
2. **Consult Reference**: Read `{SKILL_DIR}/references/repo-hygiene.md` to determine the correct Conventional Commit type.
3. **Mandatory Scan**: You MUST run a pre-commit secret scan from `{SKILL_DIR}/references/secret-scanning.md` before every commit.

## Core Competencies
- **Semantic Packaging**: Grouping Vault script refactors into logical, compliant commit blocks.
- **History Management**: Orchestrating safe rebases and branch lifecycles.
- **Integrity Scanning**: Detecting and purging inadvertent secret exposures in staged diffs.

##  Validator: Execution Verification
1. **Secret Validation**: `git diff --staged | grep -E "hvs\.|vault:v"` (Asserting empty output).
2. **Commit Integrity**: `git log -1 --pretty=%B` (Asserting match with Conventional Commits regex).
