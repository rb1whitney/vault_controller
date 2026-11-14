---
name: skill-vault-gen
description: Contract for generating credentials from templates via vault-ctl generate and config/generation_rules.yaml, followed by immediate Transit encryption.
---

# Vault Secret Generation Skill

## Contract
- **Use when**: Bootstrapping new static credentials or cloud service-account keys from a template using `config/generation_rules.yaml`.
- **Do NOT use when**: Dynamic Vault secret engines (Database/AWS/GCP leases) can be used instead, or when editing existing YAML directly (use `skill-vault-secrets`).

## Preconditions
1. Template uses `{{ rule_name(param=value) }}` syntax matching `config/generation_rules.yaml`.
2. Target cluster exists in `config/contexts.yaml`.

## Rapid Workflow
```bash
# 1. Generate YAML from template
vault-ctl generate --name <context> --template <template.yaml> --output <output.yaml>

# 2. Immediately Transit-encrypt before anything touches Git
vault-ctl secrets encrypt --path <output.yaml>

# 3. Validate and deploy
vault-ctl secrets validate --path <output.yaml>
vault-ctl secrets deploy --name <context> --path <output.yaml>
```

## Hard Don'ts
- **DO NOT** commit or leave unencrypted `<output.yaml>` in the repo after generation.
- **DO NOT** run cloud-CLI rules (`aws`, `gcloud`) without verifying the active CLI account/project is non-production or the intended target.

## Verification
- Output file contains `vault:v1:` ciphertexts and passes `vault-ctl secrets validate --path <output.yaml>`.

## References
- `references/generation-workflow.md` — Template syntax and `config/generation_rules.yaml` structure.
- **When in doubt**, prefer dynamic Vault secret engines over static generated secrets:
  - [Vault Database Secrets Engine](https://developer.hashicorp.com/vault/api-docs/secret/databases)
  - [Vault AWS Secrets Engine](https://developer.hashicorp.com/vault/api-docs/secret/aws)
  - [Vault GCP Secrets Engine](https://developer.hashicorp.com/vault/api-docs/secret/gcp)
