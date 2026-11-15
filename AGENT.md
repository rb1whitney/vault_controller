# Vault Controller

Authoritative instructions for working in `vault_controller`. Prefer the actual code in `bin/`, `lib/`, `config/`, and `tests/` over memory or assumptions.

## 1. Vault Domain & Security Guardrails

This repository implements **declarative Day-2 Vault GitOps** backed by Python `hvac` and Vault's **Transit Secrets Engine**:

1. **Transit Encryption-as-a-Service (Zero Plaintext in Git)**:
   - Secret payloads live in `config/<env>/<namespace>/` as declarative YAML.
   - Plaintext values MUST be Transit-encrypted (`vault:v1:...` ciphertext) before committing to Git.
   - Transit encryption keys used for config payloads MUST be non-exportable (`exportable: false`, `allow_plaintext_backup: false`).
   - Only CI/CD or authorized deploy operators hold decrypt/deploy permissions to push payloads into Vault.
2. **Namespace & Policy Isolation**:
   - Application teams are isolated into dedicated Vault namespaces (`_namespace` in YAML, aliased to `namespace` in Pydantic models).
   - Tenant ACL policies MUST enforce least privilege and separate read-only vs write/admin capabilities.
3. **TLS & Credential Hygiene**:
   - Always verify TLS certificates (`ca_cert` / `config/certs/ca-bundle.crt` or system trust store); never disable TLS verification in production or example configs.
   - Never log plaintext secrets, root tokens, unseal keys, or recovery keys.
   - Never assign long-lived static tokens when short-TTL or cloud/identity auth (AWS IAM, GCP, AppRole, LDAP) applies.
4. **Imperative `hvac` vs Declarative Payloads**:
   - `hvac.Client` (wrapped by `HvacClient` / `LocalVaultClient`) provides the Vault REST API surface for cluster, auth, and secret operations.
   - Declarative YAML payloads are validated by `ValidationManager` (`VaultPayload`, `ApiObject`) and transformed by `PayloadProcessor` (`Unwrap -> Transit -> Base64 -> Policy Transform`).
   - **When in doubt on endpoint semantics or parameters**, defer to [HashiCorp Vault HTTP API Docs](https://developer.hashicorp.com/vault/api-docs) and [`hvac` Documentation](https://hvac.readthedocs.io/).

---

## 2. Repository Map

- **Entrypoint (`bin/vault_ctl.py`, CLI script `vault-ctl`)**:
  - `vault-ctl cluster status|init|unseal`
  - `vault-ctl cluster rekey init|update|cancel`
  - `vault-ctl secrets validate|encrypt|decrypt|decode|encrypt-string|deploy|sync|list`
  - `vault-ctl backup`
  - `vault-ctl generate`
- **Library (`lib/`)**:
  - `lib/core/`: `HvacClient` (`hvac_client.py`), `LocalVaultClient` (`client.py`), `VaultClientAdapter` (`adapter.py`), `command.py`, `errors.py`, `logger.py`.
  - `lib/auth/`: `AuthStrategyFactory` (`factory.py`), `BaseAuthStrategy` (`base.py`), `TokenAuthStrategy` / `LDAPAuthStrategy` / `AppRoleAuthStrategy` (`standard.py`), `AWSAuthStrategy` / `GCPAuthStrategy` (`cloud.py`).
  - `lib/engines/`: `PayloadProcessor` (`payload_processor.py`) for Transit, Base64, unwrapping, and ACL policy rendering.
  - `lib/validation/`: `ValidationManager` (`manager.py`) and Pydantic models `VaultPayload` / `ApiObject` (`models.py`).
  - `lib/utils/`: `VaultSettings` / `ClusterConfig` (`settings.py`), `SecretGenerator` (`ops.py`), `crypto.py`.
- **Configuration (`config/`)**:
  - `config/contexts.yaml`: Cluster URLs, namespaces, TLS CA paths, and `recovery_key` toggle.
  - `config/generation_rules.yaml`: Rules for `vault-ctl generate`.
  - `config/certs/ca-bundle.crt`: TLS CA bundle.
  - `config/example_vault/`: Reference declarative Vault tree (`admin/`, `app1/`, `cloud-boot-app/`, `nit-fabric/`).
- **Documentation (`docs/`)**: `01_VAULT_INTRODUCTION.md` through `06_SECRET_ENCRYPTION_WORKFLOW.md` and `docs/examples/`.
- **Tests (`tests/`)**: `pytest` unit and integration suite.
- **Code Graph (`graphify-out/`)**: Pre-built Graphify knowledge graph (`graphify-out/graph.json` and `graphify-out/GRAPH_REPORT.md`).
  - Before scanning files manually, read `graphify-out/GRAPH_REPORT.md` (or query `graphify-out/graph.json` if `graphify` / `skill-graphify` is available in your harness) to orient on module hubs, dependencies, and blast radius.
- **Skills (`.agent/skills/`)**:
  - `skill-vault-lifecycle`: Cluster init, unseal, status, rekey, and Raft backup.
  - `skill-vault-secrets`: Declarative YAML payloads, KV-v2, auth methods, and Transit encryption.
  - `skill-vault-gen`: Rule-driven secret generation (`vault-ctl generate`).
  - `skill-review-suite`: `pytest`, `ruff`, and Vault security/config review checks.

---

## 3. Core Workflows

### A. Secret Lifecycle (Validate → Encrypt → Deploy)
1. Author or edit YAML payloads under `config/<env>/<namespace>/` (ensure `_namespace` matches the directory and schema matches `VaultPayload`).
2. Validate schema and guardrails:
   ```bash
   vault-ctl secrets validate --directory config/example_vault --allow-file-regex "**/*.yaml" --scheme namespaces
   ```
3. Encrypt plaintext values via Transit before committing:
   ```bash
   vault-ctl secrets encrypt --name <context> --path <target.yaml>
   ```
   Verify encrypted fields carry the `vault:v1:` prefix.
4. Deploy, list, or sync to Vault (for KV-v2 mounts, pass `metadata/`):
   ```bash
   vault-ctl secrets deploy --name <context> --path <target.yaml>
   vault-ctl secrets list --name <context> --mount <kv_mount> --path metadata/
   vault-ctl secrets sync --name <context> --source-kv <kv_mount> --source-path metadata/ --file-path <out_dir>
   ```

### B. Cluster Lifecycle & Backup
- **Status / Init / Unseal**:
  ```bash
  vault-ctl cluster status --name <context>
  vault-ctl cluster init --name <context>
  vault-ctl cluster unseal --name <context>
  ```
- **Rekey** (toggles `sys/rekey` vs `sys/rekey-recovery-key` based on `recovery_key` in `config/contexts.yaml`):
  ```bash
  vault-ctl cluster rekey init --name <context>
  vault-ctl cluster rekey update --name <context>
  vault-ctl cluster rekey cancel --name <context>
  ```
- **KV JSON Backup (LDAP-only) vs Raft Snapshots**:
  ```bash
  # KV-path JSON backup/restore (requires LDAP_USERNAME)
  vault-ctl backup backup <vault_path> <context>
  # Full Raft integrated storage snapshot
  vault operator raft snapshot save <snapshot.snap>
  ```

### C. Credential Generation
- Generate secrets from templates using `config/generation_rules.yaml`, then immediately Transit-encrypt before committing:
  ```bash
  vault-ctl generate --template <template.yaml> --output <output.yaml>
  vault-ctl secrets encrypt --path <output.yaml>
  ```

### D. Code Changes & Verification Gate
Before finishing any code or config change, run from the repository root:
```bash
pytest
ruff check .
ruff format --check .
```
All tests and lint checks must pass without skipped or relaxed assertions.

---

## 4. Non-Obvious Implementation Notes

1. **Response Resilience**: `LocalVaultClient` normalizes non-JSON or empty Vault HTTP responses (e.g., `204` / `sys/health`) into `{}` or `{"content": "..."}`.
2. **Transformation Order**: `PayloadProcessor` pipeline order is fixed (`Unwrap -> Transit -> Base64 -> Policy Transform`). Do not reorder stages.
3. **Pydantic Aliasing**: YAML files use `_namespace` (leading underscore); `VaultPayload` aliases `_namespace` to `namespace` internally.
4. **Python Path**: `pyproject.toml` sets `pythonpath = ["."]` so `lib.*` and `bin.*` imports resolve cleanly under `pytest` and standalone clones.
5. **Transit Keys Are Cluster-Local**: Ciphertexts (`vault:v1:...`) encrypted in one Vault cluster cannot be decrypted in a fresh cluster unless the same Transit key is replicated or restored.
6. **KV-v2 Listing/Sync**: `secrets list` and `secrets sync` require `--path metadata/` / `--source-path metadata/` on KV-v2 engines; default `/` is rejected by Vault.
7. **Branch Protection**: `main` is protected (`test-and-lint` CI required, direct pushes blocked). Always work on a feature branch and open a PR.
