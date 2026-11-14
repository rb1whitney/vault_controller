# Reference: Linter Mastery (Ruff)

## Code Quality Standards
Clean, consistent Python is a prerequisite for safe security tooling.

### Ruff (Python Linter & Formatter)
Ruff is configured in `pyproject.toml` (`line-length = 88`, `target-version = "py38"`).

Check and format before committing:
```bash
ruff check .
ruff format --check .
```

Auto-fix safe lint/import issues and format:
```bash
ruff check . --fix
ruff format .
```
