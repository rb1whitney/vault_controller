# Reference: Master Key Rekeying Workflows

## Workflow: Zero-Downtime Rekey
Rekeying changes the master key without re-encrypting all backend data.

### 1. Initialization
```bash
vault operator rekey -init -key-shares=5 -key-threshold=3
```
- Error 400: Already in progress. Run vault operator rekey -status to verify.

### 2. Shard Collection
Each current shard holder must provide their key:
```bash
vault operator rekey -nonce=<NONCE> <CURRENT_SHARD>
```

### 3. Verification & Distribution
Once the threshold is met, Vault outputs new shards.
- SRE Standard: New shards MUST be captured in a secure buffer and distributed immediately.
- Security Mandate: Never log the raw output of the rekey completion to persistent storage.

### Recovery: Stuck Rekey
If a rekey is initialized but cannot be completed (e.g., shard holder unavailable):
```bash
vault operator rekey -cancel
```
- Resolution: Use this to reset the state and start over with new parameters.
