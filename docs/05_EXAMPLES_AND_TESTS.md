# Examples & Operations

This guide provides explicit execution scenarios and testing protocols for the Vault controller.

---

## Content

- [The Verified Audit Landscape](#the-verified-audit-landscape)
- [Scenario 1: Foundational Control Plane Initialization](#scenario-1-foundational-control-plane-initialization)
- [Scenario 2: Identity Federation & Authentication Handshakes](#scenario-2-identity-federation--authentication-handshakes)
- [Pytest Suite & Local Integration Testing](#pytest-suite--local-integration-testing)

---

## The Verified Audit Landscape

The controller enforces a strictly declarative, stateless verification model. Every configuration change is validated against a containerized `example_vault` instance before production deployment. This eliminates configuration drift and ensures high-signal feedback during the CI lifecycle.

---

## Scenario 1: Foundational Control Plane Initialization

This profile establishes the baseline state of an unconfigured Vault node, mounting core engines and applying administrative policies.

```bash
# ------------------------------------------------------------------------------
# STEP 1: Define Unified Auth variables
# ------------------------------------------------------------------------------
export VAULT_ADDR="http://localhost:8200"
export VAULT_AUTH_TYPE="token"
export VAULT_AUTH_PRINCIPAL="admin"
export VAULT_AUTH_SECRET="hvs.root_token_here"

# ------------------------------------------------------------------------------
# STEP 2: Execute the administrative reconciliation loop
# ------------------------------------------------------------------------------
python3 bin/cluster_secret_data.py \
  --name example_vault \
  --path ./projects/vault/config/example_vault/admin
```

---

## Scenario 2: Identity Federation & Authentication Handshakes

This workflow validates integration with external identity providers (LDAP/OIDC).

```bash
# Example: Authenticating via LDAP using Unified Auth variables
export VAULT_AUTH_TYPE="ldap"
export VAULT_AUTH_PRINCIPAL="vault_admin_user"
export VAULT_AUTH_SECRET="corporate_password"

python3 bin/cluster_ops.py --name example_vault --action login
```

---

## Pytest Suite & Local Integration Testing

The `pytest` suite provides functional verification against a local `vault server -dev` environment.

### 1. Launch Ephemeral Test Container
The testing framework handles the lifecycle of the `example_vault` container automatically.

```bash
# Manual launch for interactive debugging
vault server -dev -dev-root-token-id=root -dev-listen-address=0.0.0.0:8200
```

### 2. Execute Integration Suite
The suite verifies engine provisioning, policy alignment, and `PayloadProcessor` logic.

```bash
# Set PYTHONPATH to include the project root
export PYTHONPATH=$PYTHONPATH:$(pwd)

# Run full integration suite
pytest projects/vault/tests/integration/
```

### 3. Automated Test Breakdown

| Test Component | Target Namespace | Verification Logic |
| :--- | :--- | :--- |
| `test_engine_mounting` | `sys/mounts` | Confirms engine type and versioning alignment. |
| `test_policy_idempotency` | `sys/policies/acl` | Verifies that subsequent runs do not trigger redundant API calls. |
| `test_transit_decryption` | `transit/` | Validates in-line decryption via `PayloadProcessor`. |
| `test_unified_auth` | `auth/` | Exercises multiple login strategies (AWS, Token, AppRole). |

---

## Systemic Compliance Attestation

All execution logs are captured and stored as compliance artifacts. Successful runs generate a `compliance_report.yaml` summarizing the delta operations performed on the cluster.

---
**Navigation**
- [Introduction](01_VAULT_INTRODUCTION.md)
- [Admin Guide](02_ADMIN_GUIDE.md)
- [Developer Guide](04_DEVELOPER_GUIDE.md)
