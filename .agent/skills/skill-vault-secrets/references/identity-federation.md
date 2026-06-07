# Reference: Cross-Cloud Identity Federation

## 1. AWS IAM Authentication
Maps AWS Principals (Roles/Users) to Vault Policies.

### Workflow: Authenticating from Lambda/EC2
1. Request: Application calls sts:GetCallerIdentity (signed).
2. Login: Application sends signed request to auth/aws/login.
3. Verification: Vault uses its own AWS credentials to verify the signature with AWS STS.

### Critical Resolution (403 Forbidden)
- Cause: Role name mismatch or X-Vault-AWS-IAM-Server-ID header missing.
- Fix: Verify Vault role configuration:
  ```bash
  vault read auth/aws/role/<role_name>
  ```
- SRE Standard: Always use regional STS endpoints (sts.us-east-1.amazonaws.com) to prevent DNS hijacking.

## 2. GCP Workload Identity
Uses the GCP Metadata server to establish trust.

### Workflow: Authenticating from GKE/Cloud Run
1. JWT Fetch: Application fetches an identity token from http://metadata/computeMetadata/v1/instance/service-accounts/default/identity?audience=vault/<role_name>.
2. Login: Application sends JWT to auth/gcp/login.
3. Verification: Vault verifies the JWT using GCP's public keys.

### Error Handling
- Audience Mismatch: Ensure the audience in the JWT request matches exactly what is configured in the Vault role.
- Project Boundary: Vault roles should be restricted to specific GCP Project IDs.
