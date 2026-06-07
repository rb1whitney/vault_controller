# Reference: Linter Mastery (Ruff & Markdownlint)

## 2026 Code Quality standards
Clean code is the prerequisite for security.

### 1. Ruff (Python Linter)
Ruff is the primary engine for Python quality control.
- **Rule E501**: Line too long. Wrap long f-strings or use parentheses for multiline calls.
- **Rule F401**: Unused import. Remove immediately to keep memory-agent context lean.
- **Rule I001**: Import block unsorted. Run `ruff check --fix` to automate sorting.

```bash
ruff check . --fix
ruff format .
```

### 2. Markdownlint (Documentation Quality)
Ensures documentation is professional and searchable.
- **MD013**: Line length. 
- **MD041**: First header must be a H1.
- **MD022**: Headers must be surrounded by blank lines.

```bash
markdownlint --fix .
```

### 3. Automated Resolution
Before requesting an audit, you MUST run the automated fixers. If a violation remains that cannot be fixed, you MUST document the "Technical Debt" in the PR.
