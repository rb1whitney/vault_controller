# Reference: Raft Integrated Storage Technical Specification

## Operational Endpoint: `/v1/sys/storage/raft/snapshot`
The primary method for disaster recovery and state preservation.

### Snapshot Backup: `GET`
Returns a binary stream of the cluster's integrated storage.
- **Execution Target**: MUST be sent to the **Leader** node.
- **Failure Mode**: Requests to follower nodes will return `429` or a `307 Temporary Redirect`.
- **CLI Standard**:
  ```bash
  vault operator raft snapshot save backup.snap
  ```

### Autopilot Management
Endpoint: `GET /v1/sys/storage/raft/autopilot/state`
- **Critical Metrics**:
  - `healthy`: Must be `true` for all voting nodes.
  - `failure_tolerance`: Indicates how many nodes can fail before quorum loss.

## Programmatic Best Practices
1. **Token Caching**: Vault CLI caches tokens in `~/.vault-token`. Programs should use `VAULT_TOKEN` environment variables to avoid disk persistence.
2. **Lease Handling**: Always monitor the `lease_duration` and perform `v1/sys/leases/renew` before expiration.
3. **Adaptive Overload Protection**: If receiving `503` while not sealed, check system resource metrics (CPU/RAM). Reduce request concurrency immediately.

[HashiCorp Official API Documentation](https://developer.hashicorp.com/vault/api-docs/system/storage/raft)
