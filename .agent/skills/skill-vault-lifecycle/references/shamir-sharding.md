# Reference: Shamir's Secret Sharing & Quorum Management

## 2026 Threshold Standards
Vault uses Shamir's Secret Sharing to split the master key into N shards, requiring T shards to reconstruct.

### Critical Recovery Workflows
1. Quorum Loss: If the unseal threshold cannot be met due to lost shards, the cluster is PERMANENTLY inaccessible.
   - Mitigation: Use Cloud KMS (AWS/GCP) for Auto-Unseal. 
   - Manual Shards: Store in separate physical/logical security zones.

2. Emergency Unsealing (503 Service Unavailable)
   - Trigger: Vault returns 503 while sealed.
   - Workflow:
     ```bash
     vault operator unseal <shard-1>
     vault operator unseal <shard-2>
     # Check status
     vault status -format=json | jq .sealed
     ```

### Memory Security
Vault master keys never touch the disk in plaintext.
- Barrier Key: Encrypts all data in the storage backend (Raft).
- Master Key: Encrypts the barrier key.
- Unseal Shards: Mathematically reconstruct the Master Key in memory.

### Error Codes
- 400: Missing required shard in unseal request.
- 429: Rate limiting on unseal attempts (Brute force protection).
- 500: Internal error during cryptographic reconstruction.
