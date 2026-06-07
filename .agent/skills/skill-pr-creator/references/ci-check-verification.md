# Reference: CI/CD Check Verification

## 2026 Automated Quality Gates
Never merge a PR with failing or pending required checks.

### 1. Verification via CLI
Instead of checking the web UI, use `gh` to verify status:
```bash
gh pr checks <pr-number> --watch
```
- **Wait Policy**: You must wait for all "Required" checks to turn green before passing the task to a human.

### 2. Common Failures
| Check | Meaning | Resolution |
| :--- | :--- | :--- |
| **Lint (Ruff)** | Style violation. | Run `ruff check --fix` locally and re-push. |
| **Test (Pytest)** | Functional regression. | Inspect `gh pr checks --fail` logs for traceback. |
| **Security (Checkov)** | Hardcoded secret or IMDS issue. | Resolve finding and rotate any exposed keys. |

### 3. Auditor Gate
In this repository, the `@swarm-auditor` check is a hard gate. If the `CERTIFICATION_REPORT.md` is not present and marked as `[CERTIFIED]`, the PR is structurally invalid.
