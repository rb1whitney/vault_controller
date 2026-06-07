---
name: skill-vault-lifecycle
description: Authoritative guide for Vault barrier transitions, including initialization, unsealing, and Shamir-key rotations. Triggers: vault-init, vault-unseal, vault-rekey.
---
# Vault Lifecycle Authority

## Execution Boundary
You are the master of the Barrier Transition phase. You move Vault from a dead state (Sealed/Uninitialized) to an operational state.

## Grounding Protocol
Before any lifecycle operation:
1. Sync with Binary: Run `{SKILL_DIR}/scripts/capability_discovery.sh`. This ensures Vault is installed and you know the exact flags supported by the current version.
2. Consult Reference: Read `{SKILL_DIR}/references/rekey-workflows.md` or `{SKILL_DIR}/references/shamir-sharding.md` for the exact sequence.
3. Verify Quorum: Never suggest a rekey or init without verifying vault status.

## Core Competencies
- Deterministic Init: Designing shard counts based on organizational trust models (e.g., 5/3 vs 7/5).
- Master Key Rotation: Orchestrating zero-downtime rotations via the operator rekey API.
- Unseal Automation: Troubleshooting Auto-Unseal failures (503 errors) and KMS connectivity issues.

## Validator: Finality Protocol
1. Status Assertion: vault status -format=json | jq -e '.initialized == true and .sealed == false'
2. Audit Cleanliness: Verify that no unseal keys were leaked to .bash_history or log files.
