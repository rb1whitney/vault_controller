# Declarative YAML Payload Spec (`VaultPayload`)

This repo exposes Vault mutations as declarative YAML lists of `ApiObject` entries validated by Pydantic (`lib/validation/models.py`).

## Standard Payload Shape
```yaml
# Optional namespace header (YAML MUST use _namespace with underscore)
_namespace: cloud-boot-app

api_paths:
  - api_path: v1/cloud-boot-app/data/mysql
    api_action: post
    api_payload:
      data:
        username: "vault:v1:..."
        password: "vault:v1:..."
    transit_engine: "transit"
    transit_key: "vault-admin-transit-key"
```

## Supported `ApiObject` Fields
- `api_path` (required): Vault REST path (`..` traversal rejected).
- `api_action` (required): `post`, `put`, `get`, `delete`, etc.
- `api_payload` (optional dict): Request body sent to Vault.
- `wrapped_token` (optional): Cubbyhole token unwrapped in stage 1 of `PayloadProcessor`.
- `transit_encoded_keys` / `transit_engine` / `transit_secret_engine` / `transit_key` / `transit_context`: Controls Transit encryption/decryption.
- `decode_base64_keys` (optional list): Fields Base64-decoded in stage 3.

## Repo Opinions & Guardrails
1. **No raw HCL blobs in app policies**: Express ACL policies as YAML maps under `api_payload.path` (`capabilities: ["read"]`), separating read-only app access from admin/write paths.
2. **Mount TTL cap**: Any `v1/sys/mounts/...` payload with `config.default_lease_ttl > 1h` (`3600s`) is rejected by `VaultPayload.validate_ttl`.
3. **Pipeline order is fixed**: `PayloadProcessor` executes `Unwrap -> Transit -> Base64 -> Policy Transform`.
