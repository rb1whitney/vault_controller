# Reference: Secret Generation Workflow

## Dynamic Bootstrap Logic
The Secret Generation engine enables automated creation of credentials during the "Bootstrap" phase, before they are secured for long-term storage.

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
Teams can extend the available generators by adding new entries to the `rules` mapping.
- **description**: Documentation of the rule's purpose.
- **command**: The shell command to execute. Supports `{param}` injection.
- **params**: List of required parameters for the command.

### 3. "Generate-Secure-Deploy" Pipeline
To maintain the security boundary, generated secrets MUST be transit-encrypted immediately.

**Workflow**:
1. **Generate**: `python3 bin/cluster_secret_gen.py --name example_vault --template app.template.yaml --output app.yaml`
2. **Secure**: `python3 bin/cluster_encrypt_ops.py encrypt --path app.yaml`
3. **Deploy**: `python3 bin/cluster_secret_data.py --name example_vault --path app.yaml`
