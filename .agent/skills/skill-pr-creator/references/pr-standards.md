# Reference: Semantic Pull Request Standards

## 2026 PR Architecture
A Pull Request is more than a diff; it is a permanent record of architectural decision-making.

### 1. Semantic PR Titles
Titles must match the underlying commit type: `feat:`, `fix:`, `refactor:`, `chore:`.

### 2. The Mandatory PR Template
Every PR in this repository must contain the following sections:

#### **Technical Impact**
- Describe exactly what code was changed (`bin/`, `lib/`, `tests/`).
- Mention any new dependencies introduced to `requirements.txt`.

#### **Testing Evidence**
- Provide a summary of the `pytest` output.
- Link to the `CERTIFICATION_REPORT.md` if the Auditor has already reviewed.

#### **Vault Specialist Coordination**
- For any change to `projects/vault_controller/lib/auth/` or `projects/vault_controller/bin/`, you MUST tag `@specialist-vault` as a reviewer.

### 3. CLI Workflow (gh)
```bash
gh pr create --title "feat: add GCP auth strategy" --body-file PR_BODY.md --reviewer specialist-vault
```
- **Error 422**: Branch not pushed. Execute `git push -u origin <branch>` first.
