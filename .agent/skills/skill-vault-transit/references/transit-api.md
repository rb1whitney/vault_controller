# Reference: Transit Secrets Engine Technical Specification

## API Endpoint: `POST /v1/transit/encrypt/:key_name`
Optimized for high-throughput "Encryption as a Service."

### 2026 High-Performance Pattern: `batch_input`
Always use batch processing for multiple items to minimize TLS handshake overhead.
- **Request Schema**:
  ```json
  {
    "batch_input": [
      { "plaintext": "<base64>", "context": "<base64_optional>" },
      { "plaintext": "<base64>", "context": "<base64_optional>" }
    ]
  }
  ```

### Technical Gotchas
- **207 Multi-Status**: If some items in the batch fail, Vault returns a `207` (Enterprise). You MUST inspect the individual `error` keys in the response body.
- **Base64 Validation**: If you receive a `400` error on a valid key, verify that your `plaintext` is correctly padded base64.

## Workflow: Rewrapping Ciphertext
Endpoint: `POST /v1/transit/rewrap/:key_name`
- **Purpose**: Upgrading old `vault:v1:...` ciphertexts to the latest key version.
- **Security**: The plaintext never leaves the Vault server memory.
- **Assertion**: Verify the version prefix in the response (e.g., `vault:v2:...`).

[HashiCorp Official API Documentation](https://developer.hashicorp.com/vault/api-docs/secret/transit)
