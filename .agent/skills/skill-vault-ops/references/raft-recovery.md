# Reference: Raft Quorum Recovery (Manual)

## Quorum Loss Protocol (2026 Standard)
If a Raft cluster loses a majority of nodes, it becomes non-functional.

### Manual Recovery via peers.json
1. Identify node with highest AppliedIndex (check via vault status).
2. Stop Vault service on that node.
3. Create peers.json in the raft data directory:
   ```json
   [
     {
       "id": "node-id-1",
       "address": "10.0.0.1:8201",
       "non_voter": false
     }
   ]
   ```
4. Start Vault. It will elect itself leader.
5. Immediately take a fresh snapshot: `vault operator raft snapshot save backup.snap`.

### SRE Best Practices
- Never use peers.json for normal operations.
- Always verify leader status post-recovery: `vault status -format=json | jq .leader_address`.
