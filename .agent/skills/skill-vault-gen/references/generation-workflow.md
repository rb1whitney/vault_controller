# Reference: Secret Generation Workflow

## Dynamic Bootstrap Logic
The Secret Generation engine (`lib/utils/ops.py` `SecretGenerator`) enables automated creation of credentials during bootstrapping before they are Transit-encrypted for source control.

### 1. Template Syntax
Templates use double-curly braces for rule injection:
`{{ rule_name(param1=value1, param2=value2) }}`

**Example**:
```yaml
data:
  api_token: "{{ random_string(length=32) }}"
  gcp_key: "{{ gcp_sa_key(name=vault-svc, project=my-infra) }}"
```

### 2. The Rules Engine (`config/generation_rules.yaml`)
Teams can extend available generators by adding entries to the `rules` mapping:
- **description**: Purpose of the rule.
- **command**: Command template to execute with `{param}` substitution.
- **params**: Required parameters for the command.

### 3. Generate -> Encrypt -> Deploy Pipeline
To maintain the security boundary, generated secrets MUST be Transit-encrypted before committing:

1. **Generate**: `vault-ctl generate --template app.template.yaml --output app.yaml`
2. **Encrypt**: `vault-ctl secrets encrypt --path app.yaml`
3. **Validate & Deploy**: `vault-ctl secrets validate --path app.yaml && vault-ctl secrets deploy --name example_vault --path app.yaml`
