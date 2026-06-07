---
name: skill-pr-creator
description: Manages the Pull Request lifecycle for the Vault Controller, ensuring changes are semantically titled and link to Manufacturing Tracks. Triggers: vault-pr, check-verification.
---
# PR Lifecycle Authority

## Execution Boundary
You are the master of the "Remote Transition" phase. You bridge the gap between local development and the main repository trunk.

## Grounding Protocol
Before PR creation:
1. **Sync with Binary**: Run `{SKILL_DIR}/scripts/capability_discovery.sh`. Verify `gh` has access to create PRs in this repo.
2. **Consult Reference**: Read `{SKILL_DIR}/references/pr-standards.md` to ensure the title and body are semantically compliant.
3. **Check CI**: Use `{SKILL_DIR}/references/ci-check-verification.md` to monitor checks post-creation.

## Core Competencies
- **PR Composition**: Drafting high-signal descriptions that link code changes to Manufacturing Tracks.
- **Reviewer Orchestration**: Automatically identifying and tagging the correct specialists (e.g., `@specialist-vault`).
- **Traceability**: Ensuring every PR body contains a link to the track in `{PROJECT_DIR}/conductor/tracks.md`.

##  Validator: Execution Verification
1. **PR Existence**: `gh pr list --json number,title` (Asserting current branch has an associated PR).
2. **Reviewer Assertion**: `gh pr view --json reviewRequests` (Asserting `@specialist-vault` is tagged).
