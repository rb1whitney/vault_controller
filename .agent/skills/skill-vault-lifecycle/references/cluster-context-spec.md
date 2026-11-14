# Cluster Context Spec (`config/contexts.yaml`)

This repo defines target clusters declaratively in `config/contexts.yaml` rather than passing ad-hoc URLs on the CLI.

## Schema
```yaml
clusters:
  example_vault:
    servers:
      - localhost
    api_port: "8200"
    api_url: "localhost"
    api_protocol: "http"   # Use "https" with ca_cert outside local dev
    config_env: "example_vault"
    key_holders:
      - admin@example.com
    key_threshold: 1       # Use >= 3 in multi-operator environments
    key_encrypt: false     # Set true with PGP keys in prod
    recovery_key: false    # Controls sys/rekey vs sys/rekey-recovery-key
```

## Repo Opinions
- **Single source of cluster truth**: Add new environments as keys under `clusters:` rather than hardcoding endpoints in scripts.
- **Rekey routing**: `recovery_key: true` routes `vault-ctl cluster rekey` to `v1/sys/rekey-recovery-key`; `false` routes to `v1/sys/rekey`.
- **Config tree mapping**: `config_env` maps the cluster to its declarative YAML directory under `config/<config_env>/`.
