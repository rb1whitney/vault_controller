# Graph Report - vault_controller  (2026-11-14)

## Corpus Check
- 66 files · ~21,543 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 7 file(s) not represented in the graph (top: (none) 5, .ldif 2)

## Summary
- 629 nodes · 1145 edges · 29 communities (22 shown, 7 thin omitted)
- Extraction: 85% EXTRACTED · 15% INFERRED · 0% AMBIGUOUS · INFERRED: 175 edges (avg confidence: 0.92)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `d490fbbf`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- ops.py
- AuthStrategyFactory
- LocalVaultClient
- Repository Code Map
- ValidationManager
- PayloadProcessor
- pytest
- Examples & Operations
- VaultError
- test_vault_ctl.py
- HashiCorp Vault State Controller
- VaultPayload
- Breaking the Global Lock: The Shift to Stateless, Data-Driven Vault Orchestration
- Vault Secret Generation Skill
- Vault Lifecycle Skill
- AWS EC2 Example
- Cluster Context Spec (`config/contexts.yaml`)
- 1. External Infrastructure (Kubernetes)
- Review Suite Skill
- How to get help
- Code Quality Standards
- Changelog
- vault-controller

## God Nodes (most connected - your core abstractions)
1. `Repository Code Map` - 65 edges
2. `LocalVaultClient` - 46 edges
3. `PayloadProcessor` - 42 edges
4. `ValidationManager` - 28 edges
5. `AuthStrategyFactory` - 20 edges
6. `VaultPayload` - 20 edges
7. `get_cluster()` - 18 edges
8. `2. Repository Map` - 18 edges
9. `2. Repository Map` - 18 edges
10. `VaultError` - 16 edges

## Surprising Connections (you probably didn't know these)
- `2. High-Cohesion Transport Layer: `lib/core/client.py`` --references--> `LocalVaultClient`  [INFERRED]
  docs/01_VAULT_INTRODUCTION.md → lib/core/client.py
- `Operational Core Mechanics & API Anatomy` --references--> `LocalVaultClient`  [INFERRED]
  docs/02_ADMIN_GUIDE.md → lib/core/client.py
- `Deployment Logic` --references--> `PayloadProcessor`  [INFERRED]
  docs/06_SECRET_ENCRYPTION_WORKFLOW.md → lib/engines/payload_processor.py
- `Key Technical Breakthroughs` --references--> `PayloadProcessor`  [INFERRED]
  README.md → lib/engines/payload_processor.py
- `Threat Modeling & Security Analysis` --references--> `ValidationManager`  [INFERRED]
  docs/01_VAULT_INTRODUCTION.md → lib/validation/manager.py

## Import Cycles
- None detected.

## Communities (29 total, 7 thin omitted)

### Community 0 - "ops.py"
Cohesion: 0.05
Nodes (43): backup_cmd(), convert_pgp_key(), format_key_response(), gather_pgp_keys(), backup(), _collect_leaf_paths(), encrypt_api_payload(), _get_nested_value() (+35 more)

### Community 1 - "AuthStrategyFactory"
Cohesion: 0.07
Nodes (27): 2. Repository Map, 1. External Infrastructure (Terraform), 2. Internal Vault Configuration (YAML Payload), AWS Lambda Vault Integration, 1. External Infrastructure (Kubernetes/Knative), 2. Internal Vault Configuration (YAML Payload), GCP Cloud Run Vault Integration, BaseAuthStrategy (+19 more)

### Community 2 - "LocalVaultClient"
Cohesion: 0.08
Nodes (23): Supported `ApiObject` Fields, cluster_init(), cluster_status(), cluster_unseal(), generate_secrets(), main_callback(), rekey_cancel(), rekey_init() (+15 more)

### Community 3 - "Repository Code Map"
Cohesion: 0.03
Nodes (65): bin/__init__.py, bin/vault_ctl.py, config/contexts.yaml, config/example_vault/admin/_acl_policies.yaml, config/example_vault/admin/_audit_devices.yaml, config/example_vault/admin/_auth_methods.yaml, config/example_vault/admin/_openldap_access.yaml, config/example_vault/admin/_secret_engines.yaml (+57 more)

### Community 4 - "ValidationManager"
Cohesion: 0.10
Nodes (17): 1. Plaintext Secret & Transit Checks, 2. TLS & Auth Hygiene, 3. Code & Test Integrity, Reference: Repo Security Audit Patterns, 1. Pydantic Enforcement, 2. Namespace Sovereignty, 3. Verification Metrics, Fault Isolation & Defensive Guardrails (+9 more)

### Community 5 - "PayloadProcessor"
Cohesion: 0.07
Nodes (22): The "Before and After" Pattern, The Payload Processor: Cryptographic Isolation, Content, Decryption Sequence, Encrypted Deployment Payload (YAML), In-Line Transit Decryption via PayloadProcessor, Operational Guardrails & Pipeline Verification, The Core Philosophy: Shifting Left Natively (+14 more)

### Community 6 - "pytest"
Cohesion: 0.09
Nodes (22): 1. Template Syntax, 2. The Rules Engine (`config/generation_rules.yaml`), 3. Generate -> Encrypt -> Deploy Pipeline, Dynamic Bootstrap Logic, Reference: Secret Generation Workflow, SecretGenerator, replacer(), mock_logger() (+14 more)

### Community 7 - "Examples & Operations"
Cohesion: 0.05
Nodes (36): Cloud Boot App, 📂 Directory Structure, Example Vault Configurations, NIT-Fabric, 🧠 Project-Specific Context, 🔒 Security First, Admin Guide, Content (+28 more)

### Community 8 - "VaultError"
Cohesion: 0.07
Nodes (10): VaultClientAdapter, _redact_cmd(), run(), VaultClientError, VaultError, HvacClient, get_logger(), test_run_command_failure() (+2 more)

### Community 9 - "test_vault_ctl.py"
Cohesion: 0.11
Nodes (7): mock_logger(), vault_client(), mock_settings(), test_cluster_status_down(), test_cluster_unseal(), test_secrets_deploy_logout_on_failure(), test_secrets_deploy_validation_gate_blocks_before_login()

### Community 10 - "HashiCorp Vault State Controller"
Cohesion: 0.10
Nodes (16): Contributing to Vault Controller, Documentation Styleguide, How Can I Contribute?, Pull Requests, Python Styleguide, Reporting Bugs, Styleguides, Suggesting Enhancements (+8 more)

### Community 11 - "VaultPayload"
Cohesion: 0.07
Nodes (28): 1. Vault Domain & Security Guardrails, 3. Core Workflows, 4. Non-Obvious Implementation Notes, A. Secret Lifecycle (Validate → Encrypt → Deploy), B. Cluster Lifecycle & Backup, C. Credential Generation, D. Code Changes & Verification Gate, Declarative YAML Payload Spec (`VaultPayload`) (+20 more)

### Community 12 - "Breaking the Global Lock: The Shift to Stateless, Data-Driven Vault Orchestration"
Cohesion: 0.11
Nodes (19): 1. Configuration Hub: `example_vault/`, 1. Modeling with Radius (Infrastructure-as-Application), 2. High-Cohesion Transport Layer: `lib/core/client.py`, 2. Orchestration with Airflow (The "Generate-Secure-Deploy" DAG), Architectural Blueprint & The Strategy Pattern, Breaking the Global Lock: The Shift to Stateless, Data-Driven Vault Orchestration, Content, Final Verdict (+11 more)

### Community 13 - "Vault Secret Generation Skill"
Cohesion: 0.25
Nodes (7): Contract, Hard Don'ts, Preconditions, Rapid Workflow, References, Vault Secret Generation Skill, Verification

### Community 14 - "Vault Lifecycle Skill"
Cohesion: 0.25
Nodes (7): Contract, Hard Don'ts, Preconditions, Rapid Workflow, References, Vault Lifecycle Skill, Verification

### Community 15 - "AWS EC2 Example"
Cohesion: 0.25
Nodes (7): 1. External Infrastructure (Terraform), 1. External Infrastructure (Terraform), 2. Internal Vault Configuration (YAML Payload), 2. Internal Vault Configuration (YAML Payload), AWS EC2 Example, EC2 / GCE Virtual Machine Vault Integration, GCP GCE Example

### Community 16 - "Cluster Context Spec (`config/contexts.yaml`)"
Cohesion: 0.50
Nodes (3): Cluster Context Spec (`config/contexts.yaml`), Repo Opinions, Schema

### Community 22 - "1. External Infrastructure (Kubernetes)"
Cohesion: 0.33
Nodes (5): 1. External Infrastructure (Kubernetes), 2. Internal Vault Configuration (YAML Payload), Deployment Configuration, GKE (Google Kubernetes Engine) Vault Integration, Workload Identity Setup

### Community 23 - "Review Suite Skill"
Cohesion: 0.29
Nodes (6): Contract, Hard Don'ts, Rapid Workflow, References, Review Suite Skill, Verification

### Community 24 - "How to get help"
Cohesion: 0.40
Nodes (4): General Questions, GitHub Issues, How to get help, Support

### Community 25 - "Code Quality Standards"
Cohesion: 0.50
Nodes (3): Code Quality Standards, Reference: Linter Mastery (Ruff), Ruff (Python Linter & Formatter)

### Community 26 - "Changelog"
Cohesion: 0.50
Nodes (3): Added, Changelog, [Unreleased]

## Knowledge Gaps
- **1 isolated node(s):** `vault-controller`
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 300 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **7 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `PayloadProcessor` connect `PayloadProcessor` to `ops.py`, `AuthStrategyFactory`, `LocalVaultClient`, `ValidationManager`, `Examples & Operations`, `HashiCorp Vault State Controller`, `VaultPayload`?**
  _High betweenness centrality (0.218) - this node is a cross-community bridge._
- **Are the 26 inferred relationships involving `LocalVaultClient` (e.g. with `1. Vault Domain & Security Guardrails` and `2. Repository Map`) actually correct?**
  _`LocalVaultClient` has 26 INFERRED edges - model-reasoned connections that need verification._
- **What connects `vault-controller` to the rest of the system?**
  _1 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `ops.py` be split into smaller, more focused modules?**
  _Cohesion score 0.05200341005967604 - nodes in this community are weakly interconnected._
- **Why does `LocalVaultClient` connect `LocalVaultClient` to `ops.py`, `AuthStrategyFactory`, `pytest`, `Examples & Operations`, `VaultError`, `test_vault_ctl.py`, `VaultPayload`, `Breaking the Global Lock: The Shift to Stateless, Data-Driven Vault Orchestration`?**
  _High betweenness centrality (0.129) - this node is a cross-community bridge._
- **Are the 20 inferred relationships involving `PayloadProcessor` (e.g. with `1. Vault Domain & Security Guardrails` and `2. Repository Map`) actually correct?**
  _`PayloadProcessor` has 20 INFERRED edges - model-reasoned connections that need verification._
- **Should `AuthStrategyFactory` be split into smaller, more focused modules?**
  _Cohesion score 0.07005649717514124 - nodes in this community are weakly interconnected._