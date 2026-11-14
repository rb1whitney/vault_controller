---
name: skill-vault-lifecycle
description: Contract for Vault cluster initialization, unsealing, status checks, rekeying, and Raft backups via bin/vault_ctl.py and config/contexts.yaml.
---

# Vault Lifecycle Skill

## Contract
- **Use when**: Checking cluster health, initializing or unsealing a cluster, rotating Shamir/recovery keys, or taking/restoring Raft snapshots.
- **Do NOT use when**: Authoring KV secrets, ACL policies, or Transit-encrypted YAML payloads (use `skill-vault-secrets`).

## Preconditions
1. Target cluster exists under `clusters.<name>` in `config/contexts.yaml`.
2. Auth env vars are set for authenticated ops (`VAULT_AUTH_TYPE`, `VAULT_AUTH_SECRET`, and `VAULT_AUTH_PRINCIPAL` if LDAP/AppRole).

## Rapid Workflow
```bash
# 1. Check status before any state-changing op
vault-ctl cluster status --name <context>

# 2. Init / Unseal
vault-ctl cluster init --name <context>
vault-ctl cluster unseal --name <context>

# 3. Rekey (targets sys/rekey vs sys/rekey-recovery-key via contexts.yaml recovery_key)
vault-ctl cluster rekey init --name <context>
vault-ctl cluster rekey update --name <context>
vault-ctl cluster rekey cancel --name <context>

# 4. Raft Snapshot Backup
vault-ctl backup --name <context>
```

## Hard Don'ts
- **DO NOT** run raw `vault operator ...` shell commands when `vault-ctl` supports the operation.
- **DO NOT** log or commit root tokens, unseal keys, recovery keys, or snapshot artifacts.
- **DO NOT** start a rekey without checking `recovery_key` in `config/contexts.yaml` and verifying quorum via `cluster status`.
- **DO NOT** disable TLS verification to bypass cert errors.

## Verification
- `vault-ctl cluster status --name <context>` reports initialized/unsealed healthy state.
- For backups, verify the generated snapshot file is non-empty.

## References
- `references/cluster-context-spec.md` — Repo schema and opinions for `config/contexts.yaml`.
- **When in doubt on Vault API behavior**, favor HashiCorp's official API docs:
  - [System Init (`/v1/sys/init`)](https://developer.hashicorp.com/vault/api-docs/system/init)
  - [System Unseal (`/v1/sys/unseal`)](https://developer.hashicorp.com/vault/api-docs/system/unseal)
  - [System Health (`/v1/sys/health`)](https://developer.hashicorp.com/vault/api-docs/system/health)
  - [System Rekey (`/v1/sys/rekey` & `rekey-recovery-key`)](https://developer.hashicorp.com/vault/api-docs/system/rekey)
  - [Raft Integrated Storage (`/v1/sys/storage/raft`)](https://developer.hashicorp.com/vault/api-docs/system/storage/raft)
  - [`hvac` System Backend Docs](https://hvac.readthedocs.io/en/stable/usage/system_backend/index.html)
