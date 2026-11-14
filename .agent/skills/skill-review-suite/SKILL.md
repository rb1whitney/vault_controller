---
name: skill-review-suite
description: Contract for running pytest, ruff, and Vault security/config checks before committing or opening a PR.
---

# Review Suite Skill

## Contract
- **Use when**: Completing any code, test, or `config/` YAML change before committing or opening a PR.
- **Do NOT use when**: Making read-only exploratory queries (no repo state changed).

## Rapid Workflow
```bash
pytest
ruff check .
ruff format --check .
```

## Hard Don'ts
- **DO NOT** claim tests pass if any test was skipped, relaxed, or mocked to bypass real validation/crypto logic.
- **DO NOT** allow plaintext secrets under `config/` (`vault:v1:` required for sensitive KV fields).
- **DO NOT** allow `verify=False` / `skip_verify` defaults, `exportable: true` Transit keys, or `pass` stubs in `bin/` or `lib/`.

## Verification
- `pytest` exits `0` with zero unexpected skips/failures.
- `ruff check .` and `ruff format --check .` exit `0`.
- `references/audit-patterns.md` checks report zero violations.

## References
- `references/audit-patterns.md` — Repo-specific security and anti-shortcut checks.
- `references/linter-mastery.md` — Ruff configuration and fix commands.
