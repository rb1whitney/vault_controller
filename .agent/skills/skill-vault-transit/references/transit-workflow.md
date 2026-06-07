# Reference: Transit Secrets Engine Workflow

## 2026 Crypto-Standard
Vault Transit acts as "Encryption as a Service," ensuring that sensitive data is encrypted before reaching the primary storage backend (DB/S3).

### Workflow: Batch Encryption
Processing multiple items in a single API call to reduce network overhead.
- Request Structure:
  ```json
  {
    "batch_input": [
      { "plaintext": "base64_data_1" },
      { "plaintext": "base64_data_2" }
    ]
  }
  ```
- Error Codes (Batch):
  - 400 Bad Request: One or more items in the batch failed validation.
  - 207 Multi-Status: (Enterprise 2026) Some items succeeded, some failed. Check individual error keys in the response.

### Security Best Practices
- Convergent Encryption: Use only when data deduplication or searchable indexing is required. Never use for high-entropy secrets.
- Key Derivation: Enable to generate unique working keys derived from a single backing key and a context string.
- No Disk Persistence: Plaintext data MUST exist only in volatile memory during the plaintext -> base64 -> vault API cycle.

### Common API Errors
- 503 Sealed: The cluster is sealed and cannot perform crypto operations.
- 403 Forbidden: The token lacks update permission on the transit/encrypt/<key> path.
