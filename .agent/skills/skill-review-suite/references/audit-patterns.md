# Reference: Vault Security Audit Patterns

## 2026 Anti-Shortcut Detection
The Review Suite focuses on finding faked or weakened cryptographic logic.

### 1. Hardcoded Secret Detection
Beyond pre-commit hooks, the review suite performs a secondary audit:
```bash
grep -ri "vault:v1:" example_vault/
```
- **Pattern Match**: Every secret field MUST match the `vault:v1:` prefix.
- **Violation**: Any plaintext string in a YAML file under `example_vault/` (except non-sensitive identifiers) is a critical rejection.

### 2. Logic Gap Analysis
Search for "Gutted" functions:
- **`pass` Statements**: Rejection in `bin/` or `lib/`.
- **`TODO` Markers**: Permitted only in non-critical documentation.
- **Mock Overuse**: Rejection if unit tests mock out the logic they are supposed to be testing.

### 3. TLS Compliance
- **Verify Flag**: Any `api_verify=False` or `verify=False` in `LocalVaultClient` or `VaultClientAdapter` is a critical security failure.
- **KMS/Cloud Auth**: Ensure regional endpoints are used in the new strategy implementations.
