# User Workflows

This guide outlines the self-service patterns for application teams to manage secret engines, policies, and cryptographic operations using the declarative YAML controller.

---

## Content

- [The Core Philosophy: Shifting Left Natively](#the-core-philosophy-shifting-left-natively)
- [Unified Auth & Token Handshakes](#unified-auth--token-handshakes)
- [In-Line Transit Decryption via PayloadProcessor](#in-line-transit-decryption-via-payloadprocessor)
- [Operational Guardrails & Pipeline Verification](#operational-guardrails--pipeline-verification)

---

## The Core Philosophy: Shifting Left Natively

Application teams must not interact with the Vault CLI or UI for day-2 configuration. Instead, security requirements are defined as YAML manifests within the application's repository. The controller synchronizes these manifests with the `example_vault` cluster during the deployment lifecycle.

This model decouples application code from the underlying security topology. Applications consume secrets from predictable paths initialized by the controller, using ephemeral credentials negotiated via Unified Auth.

---

## Unified Auth & Token Handshakes

Applications authenticate using the Unified Auth standard. The controller manages the initial handshake and provisions target namespace definitions based on the provided identity.

```yaml
# yaml-language-server: $schema=https://internal.platform.infra/schemas/vault-user-handshake.v1.yaml
api_objects:
  - api_method: post
    api_path: sys/validation/wrapped-token-exchange
    wrapped_token: s.A1b2C3d4E5f6G7h8I9j0K1l2
    comment: "Automatically exchanged for an active service-scoped token"
```

Execution via the controller:
```bash
export VAULT_AUTH_TYPE="approle"
export VAULT_AUTH_PRINCIPAL="app-role-id"
export VAULT_AUTH_SECRET="app-secret-id"

python3 bin/cluster_secret_data.py \
  --name example_vault \
  --path ./config/example_vault/app-deploy.yaml
```

---

## In-Line Transit Decryption via PayloadProcessor

The `projects.vault.lib.engines.payload.PayloadProcessor` manages transparent decryption of sensitive values committed to version control. This prevents plain-text secret exposure in Git.

When the controller detects values prefixed with `vault:v1:`, it routes the payload through the Transit engine before final delivery to the target KV engine.

### Encrypted Deployment Payload (YAML)

```yaml
# example-vault/cloud-boot-app/kv/db-credentials.yaml
api_paths:
  - api_path: v1/cloud-boot-app/data/mysql
    api_action: post
    api_payload:
      data:
        username: "boot_admin"
        password: "vault:v1:EnKz6XqJ+N2h6P0oY3qL...2026!" # <── SECURE CIPHERTEXT
    transit_engine: "transit"
    transit_key: "app-encryption-key"
```

### Decryption Sequence
1.  **Load**: `PayloadProcessor` identifies `transit_engine` and `transit_key` metadata.
2.  **Decrypt**: The controller calls `projects.vault.lib.engines.transit.TransitEngine.decrypt()` for all ciphertext strings.
3.  **Deliver**: The decrypted payload is POSTed to the target KV engine (e.g., `v1/cloud-boot-app/data/mysql`).
4.  **Volatile Memory**: Plain-text secrets exist only in the execution environment's memory and are never written to disk.

---

## Operational Guardrails & Pipeline Verification

Every pull request modifying a YAML manifest must pass the `pytest` validation suite. This ensures that changes do not violate organizational security policies (e.g., path overlaps or illegal capability requests).

```bash
# Validate user-submitted configurations
pytest projects/vault/tests/integration/test_user_payloads.py
```

Failure to provide a valid schema or attempting to bypass the `PayloadProcessor` will result in a non-zero exit code, blocking the deployment pipeline.

---
**Navigation**
- [Introduction](01_VAULT_INTRODUCTION.md)
- [Admin Guide](02_ADMIN_GUIDE.md)
- [Developer Guide](04_DEVELOPER_GUIDE.md)
