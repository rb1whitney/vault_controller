# Reference: Vault Error Codes and Resolution

| Code | Meaning | 2026 Resolution Workflow |
| :--- | :--- | :--- |
| 429 | Rate Limited | Implement Exponential Backoff with Jitter. Check lease_count_quota. |
| 503 | Sealed/Standby | Perform unseal workflow or verify Raft leader election. |
| 403 | Forbidden | Validate token policies. Check path prefix (e.g., v1/ vs raw). |
| 400 | Bad Request | Check batch formatting or base64 encoding integrity. |

## Recovery: Adaptive Overload Protection
If Vault returns 503 while NOT sealed, it may be under extreme resource pressure.
- Action: Reduce client request concurrency.
- Metric: Monitor `vault.runtime.num_goroutines`.
