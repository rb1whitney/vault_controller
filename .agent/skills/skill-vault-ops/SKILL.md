---
name: skill-vault-ops
description: Manages Vault cluster stability, Raft quorum health, and automated snapshot backups for state preservation. Triggers: vault-backup, raft-quorum, vault-health.
---
# Vault Operations Authority

## Execution Boundary
You are the master of the "Cluster Stability" phase. You ensure Vault remains highly available and that state is preserved through automated snapshots.

## Grounding Protocol
Before operational changes:
1. Sync with Binary: Run `{SKILL_DIR}/scripts/capability_discovery.sh`. Verify Raft autopilot settings.
2. Consult Reference: Read `{SKILL_DIR}/references/error-resolution.md` to map API errors to remediation paths.
3. Verify Snapshots: Never perform destructive maintenance without a verified Raft snapshot.

## Core Competencies
- Raft Quorum Recovery: Managing manual recovery via peers.json and recovery mode.
- State Preservation: Orchestrating `{PROJECT_DIR}/bin/cluster_backup.py` and verifying snapshot integrity.
- Cluster Health: Tuning Raft Autopilot for automated dead-server cleanup.

## Validator: Execution Verification
1. Quorum Validation: `vault operator raft list-peers -format=json | jq -e '.data.config.servers | length >= 1'`
2. Snapshot Validation: Execute `{PROJECT_DIR}/bin/cluster_backup.py` and verify file size > 0 and correct binary header.
