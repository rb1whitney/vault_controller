# Reference: Cloud Auth Method Specifications

## 1. AWS IAM Auth (`/v1/auth/aws/login`)
Requires a signed `sts:GetCallerIdentity` request payload.

### Mandatory Payload Fields
- `iam_http_request_method`: Must be `POST`.
- `iam_request_url`: Base64 encoded signed URL.
- `iam_request_body`: Base64 encoded body.
- `iam_request_headers`: Base64 encoded headers.

### Security Gotcha
- **Server ID Header**: The `X-Vault-AWS-IAM-Server-ID` header is mandatory to prevent replay attacks across different clusters.

## 2. GCP Workload Identity (`/v1/auth/gcp/login`)
Uses the GCP metadata identity token (JWT).

### Mandatory Payload Fields
- `role` (string): Vault role name.
- `jwt` (string): The identity token from the GCP metadata server.

### Critical Resolution
- **Audience**: The JWT audience MUST match the format `vault/<role_name>` if configured.
- **HTTP 403**: Usually indicates that the GCP Service Account lacks the `iam.serviceAccounts.getAccessToken` permission or the Vault role binding is incorrect.

[HashiCorp Official API Documentation](https://developer.hashicorp.com/vault/api-docs/auth/aws)
