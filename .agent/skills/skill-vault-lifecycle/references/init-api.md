# Reference: /v1/sys/init Technical Specification

## API Endpoint: `PUT /v1/sys/init`
The `/v1/sys/init` endpoint is the one-time initialization point for a new Vault cluster.

### Mandatory Parameters
- `secret_shares` (int): Number of shards to split the master key into (Standard: 5).
- `secret_threshold` (int): Shards required to reconstruct the master key (Standard: 3).

### Optional High-Security Parameters
- `pgp_keys` (array<string>): Array of PGP public keys to encrypt the output shards. 
- `stored_shares` (int): (Auto-unseal only) Number of shares to store in the unseal backend.

### Technical Gotchas
- **HTTP 400**: Cluster is already initialized. Verification: `GET /v1/sys/init` to check status.
- **Root Token Loss**: The root token is only returned ONCE during initialization. If lost, the only recovery path is through a rekey operation requiring a majority of unseal shards.
- **HCP Namespace**: If using HCP Vault Dedicated, ensure the `X-Vault-Namespace: admin` header is provided.

### CLI Parity
```bash
vault operator init -key-shares=5 -key-threshold=3
```

[HashiCorp Official API Documentation](https://developer.hashicorp.com/vault/api-docs/system/init)
