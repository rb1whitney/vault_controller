# Reference: Vault CLI Global Flags & Environment

## Mandatory Environment Variables
- `VAULT_ADDR`: Destination cluster (e.g., `https://127.0.0.1:8200`).
- `VAULT_NAMESPACE`: Mandatory for HCP/Enterprise (`admin` by default on HCP).
- `VAULT_FORMAT`: Set to `json` or `yaml` for machine-readable output.

## High-Mastery CLI Flags
- `-output-curl-string`: Essential for debugging API requests by generating the raw cURL command.
- `-output-policy`: Generates the exact HCL policy required for the current operation.
- `-wrap-ttl`: Wraps the response in a single-use token (Cubbyhole) for secure handoff.

### Exit Code Mapping
- **0**: Success.
- **1**: Local Error (Invalid flags, permission denied on local file).
- **2**: Server/Remote Error (Vault is sealed, 403 Forbidden, 404 Path Unsupported).

[HashiCorp Official CLI Documentation](https://developer.hashicorp.com/vault/docs/commands)
