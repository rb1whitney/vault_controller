---
name: skill-vault-secrets
description: Contract for authoring, validating, Transit-encrypting, and deploying declarative Vault YAML payloads via bin/vault_ctl.py.
---

# Vault Secrets & Transit Skill

## Contract
- **Use when**: Creating or modifying declarative YAML under `config/`, Transit-encrypting secrets, validating schemas, or deploying/syncing payloads to Vault.
- **Do NOT use when**: Initializing/unsealing/rekeying/backing up clusters (use `skill-vault-lifecycle`) or generating new random/cloud credentials from templates (use `skill-vault-gen`).

## Preconditions
1. Target YAML follows `VaultPayload` / `ApiObject` schema (`references/yaml-payload-spec.md`).
2. `VAULT_AUTH_TYPE` and credentials are configured for `encrypt`/`decrypt`/`deploy`/`sync`.

## Rapid Workflow
```bash
# 1. Validate schema & guardrails before network calls
vault-ctl secrets validate --path <file_or_dir>

# 2. Transit-encrypt plaintext fields in place
vault-ctl secrets encrypt --path <file_or_dir>

# 3. Verify vault:v1: ciphertext is present, then deploy/sync
vault-ctl secrets deploy --name <context> --path <file>
vault-ctl secrets sync --name <context> --path <dir>
```

## Hard Don'ts
- **DO NOT** commit or deploy KV secret YAML containing plaintext values—every secret value MUST have the `vault:v1:` prefix.
- **DO NOT** configure Transit payload keys with `exportable: true` or `allow_plaintext_backup: true`.
- **DO NOT** omit `_namespace` (leading underscore) when targeting a tenant namespace, and **DO NOT** mismatch `_namespace` against its folder.
- **DO NOT** set `default_lease_ttl > 1h` (`3600s`) on `sys/mounts` (`VaultPayload` rejects it).
- **DO NOT** reorder `PayloadProcessor` stages (`Unwrap -> Transit -> Base64 -> Policy Transform`).

## Verification
- `vault-ctl secrets validate --path <file_or_dir>` exits `0`.
- `grep -n "vault:v1:" <target.yaml>` confirms sensitive fields are encrypted before `git add`.

## References
- `references/yaml-payload-spec.md` — Repo YAML format, `VaultPayload` constraints, and Transit/ACL conventions.
- **When in doubt on Vault API behavior**, favor HashiCorp's official API docs:
  - [KV Secrets Engine v2](https://developer.hashicorp.com/vault/api-docs/secret/kv/kv-v2)
  - [Transit Secrets Engine](https://developer.hashicorp.com/vault/api-docs/secret/transit)
  - [ACL Policies (`/v1/sys/policies/acl`)](https://developer.hashicorp.com/vault/api-docs/system/policies-acl)
  - [Auth Methods (AWS / GCP / LDAP / AppRole)](https://developer.hashicorp.com/vault/api-docs/auth)
  - [Namespaces](https://developer.hashicorp.com/vault/api-docs/system/namespaces)
  - [`hvac` Secrets & Auth Docs](https://hvac.readthedocs.io/en/stable/usage/index.html)
