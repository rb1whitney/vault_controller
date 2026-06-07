# Reference: KV-V2 Secrets Engine Technical Specification

## API Path Mapping
Unlike KV-v1, KV-v2 uses specific sub-paths for different versioning operations.

### 1. Data Operations: `v1/:mount/data/:path`
Handles the retrieval and mutation of secret values.
- **GET**: Returns the secret `data` + `metadata`.
- **POST/PUT**: Creates a new version.
- **Gotcha**: `X-Vault-Namespace` is required if not in the default namespace.

### 2. Check-And-Set (CAS): `cas` parameter
Mandatory for preventing race conditions.
- If `cas: 0`, the write only succeeds if the key does not already exist.
- If `cas: N`, the write only succeeds if the current version is exactly `N`.
- **Error**: `HTTP 412 Precondition Failed` on mismatch.

### 3. Metadata & Settings: `v1/:mount/metadata/:path`
Manages version history and configuration.
- `max_versions` (int): Number of versions to retain (Default: 10).
- `cas_required` (bool): Enforces the use of `cas` for all writes.

### 4. Destruction: `v1/:mount/destroy/:path`
**Permanently deletes** specific versions.
- Request: `{ "versions": [1, 2, 3] }`
- **Gotcha**: This is a hard-delete. The data is unrecoverable.

[HashiCorp Official API Documentation](https://developer.hashicorp.com/vault/api-docs/secret/kv/kv-v2)
