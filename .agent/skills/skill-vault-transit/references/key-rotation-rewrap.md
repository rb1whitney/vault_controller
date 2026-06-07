# Reference: Key Rotation & The Rewrap Pattern

## 1. Key Rotation
Creating a new version of a cryptographic key without impacting existing ciphertexts.
```bash
vault write -f transit/keys/my-key/rotate
```
- Mechanism: New encryptions use the latest version. Old ciphertexts can still be decrypted by previous versions (unless min_decryption_version is set).

## 2. The Rewrap Protocol (SOTA 2026)
Upgrading old ciphertexts to the latest key version. This is critical for post-compromise mitigation or compliance (PCI/SOC2).

### Execution Flow:
1. Identify: Detect vault:v1:... ciphertexts in the database.
2. Rewrap API: Send ciphertexts to transit/rewrap/my-key.
   - Vault decrypts with v1 and re-encrypts with v2 INTERNALLY.
   - Plaintext NEVER leaves the Vault memory space.
3. Update: Receive vault:v2:... and update the database record.

### Security Hardening
Once rewrap is complete for all records:
```bash
vault write transit/keys/my-key/config min_decryption_version=2
```
- Result: Any stolen v1 ciphertexts are now cryptographically "dead."
