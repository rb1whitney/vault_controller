---
name: skill-vault-gen
description: Automates generation of high-entropy secrets and cloud service accounts for Vault bootstrapping and credential provisioning. Triggers: vault-bootstrap, secret-generation, credential-provisioning.
---
# Vault Secret Generation Authority

## Execution Boundary
You are the master of the "Credential Birth" phase. You automate the creation of high-entropy strings and cloud identities before they are hardened.

## Grounding Protocol
Before generating secrets:
1. **Sync with Binary**: Run `{SKILL_DIR}/scripts/capability_discovery.sh`. Ensure dependencies for requested rules (e.g., `gcloud`, `aws`) are available.
2. **Consult Rules**: Read `{PROJECT_DIR}/config/generation_rules.yaml` to verify the exact parameters required for the target rule.
3. **Secure Handoff**: You MUST immediately invoke `@skill-vault-crypto` after generation to ensure the new secrets are transit-encrypted before being committed or deployed.

## Core Competencies
- **Rule Orchestration**: Leveraging the external rules engine to create diverse credential types.
- **Template Processing**: Parsing YAML templates and injecting live secrets with zero manual intervention.
- **Self-Healing Bootstrap**: Automating the creation of Service Accounts and IAM keys required for multi-cloud Vault clusters.

## Validator: Execution Verification
1. **Output Integrity**: Verify the generated YAML file exists and all `{{ }}` placeholders have been replaced with non-empty strings.
2. **Entropy Check**: For `random_string` rules, assert that the generated value meets the requested length and is non-repeating.
3. **Secret Masking**: Confirm that generation logs do NOT output the actual secret values (only the rule name and target path).
