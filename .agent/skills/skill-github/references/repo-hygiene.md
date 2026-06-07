# Reference: Repository Hygiene & Semantic Commits

## 2026 Git Standards
Maintaining a clean, immutable history is mandatory for automated auditing.

### 1. Branching Strategy
- **Feature Isolation**: Never work directly on `main`. Create scoped branches: `feat/vault-rekey-logic` or `fix/ldap-path-error`.
- **Rebase Workflow**: Use `git rebase main` to maintain a linear history. Avoid merge commits for internal project updates.

### 2. Semantic Commits (Conventional Commits)
Commits must follow the `<type>(<scope>): <description>` format for automated changelog generation.

| Type | Meaning |
| :--- | :--- |
| **feat** | A new feature or script implementation. |
| **fix** | A bug fix or technical debt resolution. |
| **docs** | Documentation-only changes. |
| **chore** | Maintenance tasks (dependency updates, linting). |
| **refactor** | Code changes that neither fix a bug nor add a feature. |

### 3. Repository Cleanup
- **Stale Branches**: Delete local and remote branches immediately after successful merge.
- **Large Files**: Never commit binaries or large Raft snapshots to Git. Use `git-lfs` or external S3/GCS storage.
