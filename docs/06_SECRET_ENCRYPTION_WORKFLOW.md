# Secret Encryption Workflow

Committing plain-text secrets to version control is a critical security failure. This repository utilizes the **HashiCorp Vault Transit Engine** to encrypt sensitive values before they are committed.

---

## The Encryption Pattern

Developers must transform plain-text YAML payloads into secure, encrypted manifests using the `bin/cluster_encrypt_ops.py` utility.

### 1. Plain-text Manifest (Local Only)
**NEVER COMMIT THIS.**

```yaml
# example-vault/cloud-boot-app/kv/mysql-credentials.yaml
api_paths:
  - api_path: v1/cloud-boot-app/data/mysql
    api_action: post
    api_payload:
      data:
        username: "boot_admin"
        password: "VaultPassword2026!" # <── EXPOSED SECRET
```

### 2. Encrypted Manifest (Production Ready)
**SAFE TO COMMIT.**

```yaml
# example-vault/cloud-boot-app/kv/mysql-credentials.yaml
api_paths:
  - api_path: v1/cloud-boot-app/data/mysql
    api_action: post
    api_payload:
      data:
        username: "boot_admin"
        password: "vault:v1:EnKz6XqJ+N2h6P0oY3qL...2026!" # <── SECURE CIPHERTEXT
    transit_engine: "transit"
    transit_key: "vault-admin-transit-key"
```

---

## Automated Secret Bootstrapping (Optional)

Ideally, applications should utilize **Dynamic Secret Engines** (Database, AWS, GCP) to eliminate static credentials entirely. However, for applications not yet built to manage Vault leases or native handshakes, we provide the `bin/cluster_secret_gen.py` engine.

This tool automates the "Birth" of static secrets from an extensible rules engine.

```bash
# Generate secrets from a template before securing them
python3 bin/cluster_secret_gen.py --name example_vault \
  --template ./projects/vault/config/example_vault/templates/db.yaml \
  --output ./projects/vault/config/example_vault/cloud-boot-app/kv/db.yaml
```

Once generated, proceed to the encryption workflow below to secure the results for source control.

---

## Execution: Encrypting Local Payloads

Use the `bin/cluster_encrypt_ops.py` tool. This script utilizes `projects.vault.lib.engines.transit` to perform cryptographic operations.

### Step 1: Configure Unified Auth
```bash
export VAULT_AUTH_TYPE="token"
export VAULT_AUTH_PRINCIPAL="admin"
export VAULT_AUTH_SECRET="your-access-token"
```

### Step 2: Run Encryption Command
```bash
python3 bin/cluster_encrypt_ops.py --name example_vault encrypt \
  --path ./projects/vault/config/example_vault/cloud-boot-app/kv/mysql-credentials.yaml \
  --transit-key "vault-admin-transit-key"
```

The encryption logic:
1.  Loads the YAML manifest.
2.  Base64-encodes sensitive fields within `api_payload`.
3.  Calls the Transit engine via `projects.vault.lib.core.client.VaultClient`.
4.  Overwrites the local file with encrypted ciphertext.
5.  Injects required metadata (`transit_engine`, `transit_key`) for the deployment controller.

---

## Deployment Logic

The `bin/cluster_secret_data.py` controller detects the `transit_engine` metadata and invokes the `PayloadProcessor` to perform in-line decryption during the reconciliation loop.

```bash
# Transparently decrypts and deploys secrets
python3 bin/cluster_secret_data.py \
  --name example_vault \
  --path ./projects/vault/config/example_vault/cloud-boot-app/kv/
```

Verification of the encryption/decryption lifecycle is handled by `pytest`:
```bash
pytest projects/vault/tests/integration/test_encryption_workflow.py
```

---
**Navigation**
- [User Workflows](03_USER_WORKFLOWS.md)
- [Examples & Tests](05_EXAMPLES_AND_TESTS.md)
