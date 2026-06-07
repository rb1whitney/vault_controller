# Example Vault Configurations

This directory contains real-world Vault configuration payloads (YAML) derived from active projects in this repository. Use these as a reference for your own secret management implementations.

## 📂 Directory Structure

```bash
example_vault/
├── admin/               # Core cluster administration (Audit, Auth, Engines)
├── app1/                # Legacy application examples
├── cloud-boot-app/      # Spring Boot application secrets & policies
│   └── kv/              # Transit-encrypted secrets
└── nit-fabric/          # Multi-cloud governance engine credentials
    └── kv/              # Transit-encrypted secrets
```

## 🔒 Security First

All payloads in this directory (except `admin/`) are **Transit Encrypted**. They cannot be read without access to the `vault-admin-transit-key` on the target cluster.

See [**docs/06_SECRET_ENCRYPTION_WORKFLOW.md**](../../docs/06_SECRET_ENCRYPTION_WORKFLOW.md) for the "Before and After" guide on taking plain-text secrets and securing them for commit.

Apply any of these configurations using the `bin/cluster_secret_data.py` tool.

**Example**: Initialize the Cloud Boot App environment:
```bash
# 1. Mount engines and policies
python3 bin/cluster_secret_data.py --name example_vault --path ./config/example_vault/cloud-boot-app/

# 2. Write specific secret data
python3 bin/cluster_secret_data.py --name example_vault --path ./config/example_vault/cloud-boot-app/db-credentials.yaml
```

## 🧠 Project-Specific Context

### Cloud Boot App
Optimized for **Spring Boot 4** integration.
- **`db-credentials.yaml`**: Demonstrates structured JSON storage for JDBC connections.
- **`api-keys.yaml`**: Centralized storage for high-value external tokens (Stripe, Twilio).

### NIT-Fabric
Optimized for **Multi-Cloud Governance**.
- **`cloud-credentials.yaml`**: Shows how to store both AWS IAM keys and complex GCP Service Account JSON payloads in a single KV-V2 path.
- **`_acl_policies.yaml`**: Grants the least-privileged `governor` role access to cloud credentials and the Transit encryption backend.

---
*Note: All sensitive values here are placeholders. Never commit actual production secrets to this directory.*
