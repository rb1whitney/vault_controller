# Reference: KV-V2 Secrets Management Mastery

## Versioning & Data Protection
KV-V2 supports multiple versions for every key, enabling disaster recovery and rollback.

### 1. Versioned Retrieval
```bash
vault kv get -version=5 secret/my-app
```

### 2. Check-And-Set (CAS)
Prevents race conditions where two clients overwrite the same secret simultaneously.
- Mechanism: Provide the cas parameter (current version number).
- Behavior: If the provided cas doesn't match the latest version on the server, the write is REJECTED.

### 3. Deletion vs. Destruction
- Delete: Marks a version as deleted but the data remains in the backend (recoverable).
- Destroy: PERMANENTLY erases the data from the storage backend (non-recoverable).
- Metadata: Even if data is destroyed, the version history (metadata) remains unless metadata delete is called.

### Error Codes
- 404 Not Found: Path does not exist OR the token lacks list/read permissions.
- 403 Forbidden: Token has no access to this specific version or mount.
- 412 Precondition Failed: CAS mismatch during a write operation.
