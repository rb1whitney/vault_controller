# GCP Cloud Run Vault Integration

This example demonstrates how to deploy a Cloud Run service configured to authenticate with Vault using the `GCPAuthStrategy`. 
The strategy uses the attached service account to generate a signed JWT, which Vault validates.

## 1. External Infrastructure (Kubernetes/Knative)

```yaml
apiVersion: serving.knative.dev/v1
kind: Service
metadata:
  name: vault-automation-service
spec:
  template:
    spec:
      # Attach a specific service account that Vault is configured to trust
      serviceAccountName: vault-automation-sa@my-project.iam.gserviceaccount.com
      containers:
      # Enforce immutable artifacts via SHA256 digest
      - image: gcr.io/my-project/vault-worker@sha256:1a2b3c4d5e6f...
        env:
        # Unified Vault Auth Configuration
        - name: VAULT_AUTH_TYPE
          value: "gcp"
        # The principal is the name of the role configured in Vault's GCP auth backend
        - name: VAULT_AUTH_PRINCIPAL
          value: "cloud-run-automation-role"
        # VAULT_AUTH_SECRET is not needed; the strategy fetches the JWT dynamically via the metadata server
```

## 2. Internal Vault Configuration (YAML Payload)

To allow the Cloud Run service to authenticate, configure the `gcp` auth method inside Vault mapping to the Google Service Account.

**Example Payload (`example_vault/admin/_auth_methods.yaml`)**:
```yaml
api_paths:
- api_path: v1/auth/gcp/role/cloud-run-automation-role
  api_action: post
  api_payload:
    type: "gce"
    project_id: "my-project"
    bound_service_accounts: "vault-automation-sa@my-project.iam.gserviceaccount.com"
    policies: "automation-policy"
```

You apply this configuration by running:
```bash
python3 bin/cluster_secret_data.py --name example_vault --path ./config/example_vault/admin/_auth_methods.yaml
```
