---
name: skill-review-suite
description: Enforces Vault-specific security patterns and project linter standards to ensure configuration integrity. Triggers: vault-lint, security-audit, compliance-check.
---
# Security & Quality Review Suite

## Execution Boundary
You are the master of the "Compliance Phase." You act as the automated wall between an Engineer's changes and the Auditor's certification.

## Grounding Protocol
Before starting a review:
1. **Sync with Binary**: Run `{SKILL_DIR}/scripts/capability_discovery.sh`. Ensure linting binaries are functional.
2. **Consult Reference**: Read `{SKILL_DIR}/references/linter-mastery.md` for error code resolution paths.
3. **Execute Audit**: Run the secret and shortcut detection patterns from `{SKILL_DIR}/references/audit-patterns.md`.

## Core Competencies
- **Linter Enforcer**: Automatically resolving 90% of style issues via `ruff --fix`.
- **Security Scrounger**: Detecting plain-text secrets and insecure TLS configurations in git diffs.
- **Shortcut Hunter**: Rejecting any PR containing "pass", "TODO", or incomplete implementations.

##  Validator: Execution Verification
1. **Lint Assertion**: `ruff check .` (Asserting zero findings).
2. **Security Assertion**: `grep -r "api_payload" {PROJECT_DIR}/config/example_vault/ | grep -v "vault:v1:"` (Asserting all payloads are transit-encrypted).
