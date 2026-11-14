# GKE (Google Kubernetes Engine) Vault Integration

This example shows how to configure a Kubernetes Deployment in GKE to authenticate to Vault.
Here we demonstrate the `gcp` strategy utilizing Workload Identity.

## 1. External Infrastructure (Kubernetes)

### Workload Identity Setup
Ensure your Kubernetes Service Account (KSA) is bound to a Google Service Account (GSA) within a dedicated application namespace:

```bash
kubectl create namespace vault-ops
kubectl create serviceaccount ksa-vault-worker --namespace vault-ops

kubectl annotate serviceaccount ksa-vault-worker \
    --namespace vault-ops \
    iam.gke.io/gcp-service-account=vault-automation-sa@my-project.iam.gserviceaccount.com
```

### Deployment Configuration
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: vault-worker-deployment
  namespace: vault-ops
spec:
  replicas: 1
  selector:
    matchLabels:
      app: vault-worker
  template:
    metadata:
      labels:
        app: vault-worker
    spec:
      # Bind to the annotated Kubernetes Service Account
      serviceAccountName: ksa-vault-worker
      containers:
      - name: worker
        image: gcr.io/my-project/vault-worker:latest
        env:
        # Unified Vault Auth Configuration
        - name: VAULT_AUTH_TYPE
          value: "gcp"
        - name: VAULT_AUTH_PRINCIPAL
          value: "gke-automation-role"
```

## 2. Internal Vault Configuration (YAML Payload)

Configure the `gcp` auth method inside Vault to trust the underlying Google Service Account.

**Example Payload (`example_vault/admin/_auth_methods.yaml`)**:
```yaml
api_paths:
- api_path: v1/auth/gcp/role/gke-automation-role
  api_action: post
  api_payload:
    type: "iam"
    project_id: "my-project"
    bound_service_accounts: "vault-automation-sa@my-project.iam.gserviceaccount.com"
    policies: "automation-policy"
```

You apply this configuration by running:
```bash
python3 bin/vault_ctl.py secrets deploy --name example_vault --path ./config/example_vault/admin/_auth_methods.yaml
```
