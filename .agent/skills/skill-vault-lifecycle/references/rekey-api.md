# Reference: /v1/sys/rekey Technical Specification

## Rekeying Lifecycle
Rekeying rotates the Master Key (or Recovery Key) without re-encrypting the data in the storage backend.

### Endpoint: `PUT /v1/sys/rekey/init`
Starts a rekeying attempt.
- `secret_shares` (int): New total shards.
- `secret_threshold` (int): New required shards.

### Endpoint: `PUT /v1/sys/rekey/update`
Submits a current unseal shard to the process.
- `key` (string): The current unseal shard.
- `nonce` (string): The nonce returned by the `init` call.

### Operational Resolution
- **HTTP 400 (Conflict)**: A rekey is already in progress.
- **Command**: `vault operator rekey -status` to see current progress.
- **Workflow**: If a shard holder is missing, use `PUT /v1/sys/rekey/cancel` to reset.

[HashiCorp Official API Documentation](https://developer.hashicorp.com/vault/api-docs/system/rekey)
