# Reference: Repo Security Audit Patterns

## 1. Plaintext Secret & Transit Checks
Verify sensitive KV payloads under `config/` use `vault:v1:` ciphertext and Transit keys are hardened:
```bash
grep -rn "vault:v1:" config/example_vault/
grep -rn "exportable" config/
```
- **Required**: KV secret fields carry `vault:v1:` prefix.
- **Violation**: Plaintext passwords/keys in `config/` YAML, or `exportable: true` / `allow_plaintext_backup: true` on Transit keys.

## 2. TLS & Auth Hygiene
- **Verify Flag**: Reject `verify=False`, `api_verify=False`, or `skip_verify` defaults in `lib/` or `config/`.
- **Log Redaction**: Never log `api_payload`, tokens, unseal keys, or decrypted secrets.

## 3. Code & Test Integrity
- Reject gutted `pass` bodies in `bin/` or `lib/`.
- Reject tests that mock out the exact `ValidationManager` or `PayloadProcessor` behavior they claim to verify.
