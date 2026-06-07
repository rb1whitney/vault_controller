# Reference: Pre-Commit Secret Scanning Protocols

## 2026 Leak Prevention
Vault repositories are high-value targets. Automated pre-commit scanning is the first line of defense.

### 1. Signature Patterns
Scan all staged changes for known Vault and Cloud credential formats.

| Pattern | Regex | Risk |
| :--- | :--- | :--- |
| **Vault Token** | `hvs\.[a-zA-Z0-9_-]{20,}` | Root/Admin Access |
| **Vault Transit** | `vault:v[0-9]:[a-zA-Z0-9+/=]+` | Plaintext Exposure |
| **AWS Access Key** | `AKIA[0-9A-Z]{16}` | Cloud Compromise |
| **GCP SA Key** | `"type":\s*"service_account"` | Infrastructure Takeover |

### 2. Local Scan Workflow
Before running `git commit`, execute a targeted grep on staged chunks:
```bash
git diff --staged | grep -Ei "hvs\.|vault:v|AKIA|service_account"
```

### 3. Remediation: Accidental Commit
If a secret is committed but not pushed:
1. **Reset**: `git reset --soft HEAD~1`
2. **Clean**: Remove the secret from the file.
3. **Re-Add**: `git add <file>`
4. **Re-Commit**: Ensure the secret is purged from the working tree.

*If pushed to remote, the secret is COMPROMISED. Rotate immediately.*
